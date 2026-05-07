"""Google Drive watcher — register webhooks, filter transcript files, download content."""
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import DriveWebhook, OAuthToken, Meeting

logger = logging.getLogger(__name__)

TRANSCRIPT_NAME_PATTERN = re.compile(r"meet\s*transcript", re.IGNORECASE)
ALLOWED_EXTENSIONS = {".docx", ".txt", ".vtt"}
MEET_RECORDINGS_FOLDER = "Meet Recordings"


def _get_drive_service(access_token: str):
    """Build a Google Drive API v3 service using the user's access token."""
    creds = Credentials(token=access_token)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


async def get_refreshed_token(token: OAuthToken, db: AsyncSession) -> str:
    """Return a valid access token, refreshing if expired."""
    if token.expires_at and token.expires_at > datetime.now(timezone.utc):
        return token.access_token

    if not token.refresh_token:
        logger.warning(f"No refresh token for user {token.user_id}, using existing access token")
        return token.access_token

    try:
        creds = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )
        creds.refresh(GoogleAuthRequest())

        token.access_token = creds.token
        token.expires_at = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None
        token.updated_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(f"Refreshed OAuth token for user {token.user_id}")
        return creds.token
    except Exception as e:
        logger.error(f"Failed to refresh token for user {token.user_id}: {e}")
        return token.access_token


async def register_webhook(user_id: str, access_token: str, db: AsyncSession) -> dict:
    """Register a Drive push notification channel for a user."""
    channel_id = str(uuid.uuid4())
    webhook_url = f"{settings.webhook_base_url}/webhooks/drive"

    service = _get_drive_service(access_token)

    # Watch for changes on the user's Drive
    body = {
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_url,
        "expiration": int(
            (datetime.now(timezone.utc) + timedelta(days=7)).timestamp() * 1000
        ),
    }

    response = service.changes().watch(
        pageToken="1", body=body
    ).execute()

    # Store webhook registration
    webhook = DriveWebhook(
        user_id=user_id,
        channel_id=channel_id,
        resource_id=response.get("resourceId"),
        expiry=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(webhook)
    await db.commit()

    return {"channel_id": channel_id, "resource_id": response.get("resourceId")}


async def renew_expiring_webhooks(db: AsyncSession):
    """Find webhooks expiring within 24 hours and re-register them."""
    threshold = datetime.now(timezone.utc) + timedelta(hours=24)
    result = await db.execute(
        select(DriveWebhook).where(DriveWebhook.expiry < threshold)
    )
    expiring = result.scalars().all()

    for webhook in expiring:
        # Get the user's access token
        token_result = await db.execute(
            select(OAuthToken).where(OAuthToken.user_id == webhook.user_id)
        )
        token = token_result.scalar_one_or_none()
        if not token:
            continue

        # Stop old channel
        try:
            service = _get_drive_service(token.access_token)
            service.channels().stop(body={
                "id": webhook.channel_id,
                "resourceId": webhook.resource_id,
            }).execute()
        except Exception:
            pass  # Old channel may have already expired

        # Register new one
        await register_webhook(str(webhook.user_id), token.access_token, db)

        # Remove old record
        await db.delete(webhook)
        await db.commit()


def is_transcript_file(file_metadata: dict) -> bool:
    """Check if a Drive file is a Google Meet transcript we should process."""
    name = file_metadata.get("name", "")
    mime = file_metadata.get("mimeType", "")

    # Check name contains "Meet Transcript" (case-insensitive)
    if not TRANSCRIPT_NAME_PATTERN.search(name):
        return False

    # Check extension or MIME type
    name_lower = name.lower()
    has_valid_ext = any(name_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)
    is_google_doc = mime == "application/vnd.google-apps.document"

    if not has_valid_ext and not is_google_doc:
        return False

    # Check if in Meet Recordings folder (via parents)
    parents = file_metadata.get("parents", [])
    # Parents check happens at a higher level where we can query folder name

    return True


def is_in_meet_recordings_folder(file_metadata: dict, service) -> bool:
    """Check if file's parent folder is named 'Meet Recordings'."""
    parents = file_metadata.get("parents", [])
    if not parents:
        return True  # Allow files without parent info (permissive)

    for parent_id in parents:
        try:
            folder = service.files().get(
                fileId=parent_id, fields="name"
            ).execute()
            if folder.get("name") == MEET_RECORDINGS_FOLDER:
                return True
        except Exception:
            continue

    return False


async def is_already_processed(drive_file_id: str, db: AsyncSession) -> bool:
    """Check if we've already processed this file (idempotency)."""
    result = await db.execute(
        select(Meeting).where(Meeting.drive_file_id == drive_file_id)
    )
    return result.scalar_one_or_none() is not None


def download_transcript(access_token: str, file_id: str, mime_type: str) -> str:
    """Download file content from Google Drive. Exports Google Docs as plain text."""
    service = _get_drive_service(access_token)

    if mime_type == "application/vnd.google-apps.document":
        # Export Google Doc as plain text
        response = service.files().export(
            fileId=file_id, mimeType="text/plain"
        ).execute()
        return response.decode("utf-8") if isinstance(response, bytes) else response
    else:
        # Download raw file
        response = service.files().get_media(fileId=file_id).execute()
        return response.decode("utf-8") if isinstance(response, bytes) else response


async def get_changed_files(access_token: str, page_token: str = "1") -> list[dict]:
    """Fetch recently changed files from a user's Drive."""
    service = _get_drive_service(access_token)

    results = []
    response = service.changes().list(
        pageToken=page_token,
        fields="changes(fileId,file(id,name,mimeType,parents,modifiedTime)),newStartPageToken",
        includeRemoved=False,
    ).execute()

    for change in response.get("changes", []):
        file_meta = change.get("file")
        if file_meta and is_transcript_file(file_meta):
            if is_in_meet_recordings_folder(file_meta, service):
                results.append(file_meta)

    return results
