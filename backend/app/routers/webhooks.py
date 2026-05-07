"""Webhook endpoints — receives Google Drive push notifications."""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DriveWebhook, OAuthToken
from app.database.postgres import get_db
from app.services.drive_watcher import (
    download_transcript,
    get_changed_files,
    is_already_processed,
)
from app.services.transcript_processor import process_transcript

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def _process_transcript_background(
    user_id: str, access_token: str, file_id: str, mime_type: str, file_name: str
):
    """Background task: download transcript and run processing pipeline."""
    try:
        content = download_transcript(access_token, file_id, mime_type)
        logger.info(
            f"Downloaded transcript: {file_name} ({len(content)} chars) for user {user_id}"
        )

        # Run the full processing pipeline with a new DB session
        from app.database.postgres import async_session
        async with async_session() as db:
            await process_transcript(user_id, file_id, file_name, content, db)

    except Exception as e:
        logger.error(f"Failed to process transcript {file_id}: {e}")


@router.post("/drive")
async def drive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    x_goog_channel_id: str = Header(None),
    x_goog_resource_state: str = Header(None),
    x_goog_resource_id: str = Header(None),
):
    """
    Receive Google Drive push notification.

    Google sends two types:
    - sync: initial verification (respond 200 immediately)
    - change: a file was created/modified
    """
    # Respond to sync notifications immediately
    if x_goog_resource_state == "sync":
        return Response(status_code=200)

    # Validate the channel exists in our database
    if not x_goog_channel_id:
        return Response(status_code=400)

    result = await db.execute(
        select(DriveWebhook).where(DriveWebhook.channel_id == x_goog_channel_id)
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        logger.warning(f"Unknown channel_id: {x_goog_channel_id}")
        return Response(status_code=404)

    # Get the user's access token
    token_result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == webhook.user_id)
    )
    token = token_result.scalar_one_or_none()

    if not token:
        logger.error(f"No OAuth token for user {webhook.user_id}")
        return Response(status_code=200)  # Ack to prevent retries

    # Fetch changed files that match our transcript filter
    try:
        changed_files = await get_changed_files(token.access_token)
    except Exception as e:
        logger.error(f"Failed to fetch changed files: {e}")
        return Response(status_code=200)  # Ack anyway

    # Queue each new transcript for processing
    for file_meta in changed_files:
        file_id = file_meta["id"]

        # Idempotency: skip if already processed
        if await is_already_processed(file_id, db):
            logger.info(f"Skipping already-processed file: {file_id}")
            continue

        background_tasks.add_task(
            _process_transcript_background,
            user_id=str(webhook.user_id),
            access_token=token.access_token,
            file_id=file_id,
            mime_type=file_meta.get("mimeType", ""),
            file_name=file_meta.get("name", ""),
        )

    return Response(status_code=200)
