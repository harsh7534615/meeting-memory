"""
Weekly digest — compiles meeting summaries into a structured digest email.

- Fetches all meetings from past 7 days for a user
- Compiles: decisions, open questions, action items, topics
- Calls Gemini to produce structured digest
- Sends via Resend
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import google.generativeai as genai
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Meeting, User

logger = logging.getLogger(__name__)

DIGEST_PROMPT = """You are a meeting assistant. Given the summaries of meetings from the past week, produce a structured weekly digest.

Format the digest with these sections:
## Key Decisions
- List each decision made across all meetings

## Action Items
- List each action item with the person responsible

## Open Questions
- List any unresolved questions or topics that need follow-up

## Topics Discussed
- Brief list of major topics covered

Be concise. Use bullet points. Only include items actually mentioned in the summaries.

Meeting summaries from this week:
{summaries}

Weekly Digest:"""


async def generate_digest(user_id: str, db: AsyncSession) -> Optional[dict]:
    """
    Generate a weekly digest for a user.

    Returns dict with: { subject, body_text, meetings_count }
    or None if no meetings in the past week.
    """
    # Fetch meetings from past 7 days
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    result = await db.execute(
        select(Meeting)
        .where(
            and_(
                Meeting.user_id == user_id,
                Meeting.processed_at >= one_week_ago,
            )
        )
        .order_by(Meeting.meeting_date.desc())
    )
    meetings = result.scalars().all()

    if not meetings:
        return None

    # Compile summaries
    summaries_text = ""
    for m in meetings:
        title = m.title or "Untitled Meeting"
        date = str(m.meeting_date) if m.meeting_date else "Unknown date"
        participants = ", ".join(m.participant_names) if m.participant_names else "Unknown"
        summary = m.summary or "No summary available."

        summaries_text += f"\n### {title} ({date})\nParticipants: {participants}\n{summary}\n"

    # Generate digest via Gemini
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)

    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = DIGEST_PROMPT.format(summaries=summaries_text)
    response = model.generate_content(prompt)
    digest_body = response.text

    # Get user info for subject line
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    user_name = user.name.split(" ")[0] if user and user.name else "there"

    subject = f"Your weekly meeting digest — {len(meetings)} meeting{'s' if len(meetings) != 1 else ''} this week"

    return {
        "subject": subject,
        "body_text": digest_body,
        "body_html": _to_html(digest_body, user_name, len(meetings)),
        "meetings_count": len(meetings),
    }


async def send_digest_email(user_id: str, db: AsyncSession) -> bool:
    """Generate and send the weekly digest email for a user."""
    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.digest_enabled:
        return False

    digest = await generate_digest(user_id, db)
    if not digest:
        logger.info(f"No meetings for user {user_id} this week, skipping digest")
        return False

    # Send via Resend
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set, skipping email send")
        return False

    try:
        import resend
        resend.api_key = settings.resend_api_key

        resend.Emails.send({
            "from": "Meeting Memory <digest@meetingmemory.app>",
            "to": [user.email],
            "subject": digest["subject"],
            "html": digest["body_html"],
        })
        logger.info(f"Sent digest to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send digest to {user.email}: {e}")
        return False


async def send_all_digests(db: AsyncSession):
    """Send digests to all users with digest_enabled=True."""
    result = await db.execute(
        select(User).where(User.digest_enabled == True)  # noqa: E712
    )
    users = result.scalars().all()

    for user in users:
        try:
            await send_digest_email(str(user.id), db)
        except Exception as e:
            logger.error(f"Digest failed for user {user.id}: {e}")


def _to_html(markdown_text: str, user_name: str, meeting_count: int) -> str:
    """Convert digest markdown to a simple HTML email."""
    # Basic markdown → HTML conversion
    html_body = markdown_text
    html_body = html_body.replace("## Key Decisions", "<h2 style='color:#1e293b;font-size:18px;margin-top:24px;'>🎯 Key Decisions</h2>")
    html_body = html_body.replace("## Action Items", "<h2 style='color:#1e293b;font-size:18px;margin-top:24px;'>✅ Action Items</h2>")
    html_body = html_body.replace("## Open Questions", "<h2 style='color:#1e293b;font-size:18px;margin-top:24px;'>❓ Open Questions</h2>")
    html_body = html_body.replace("## Topics Discussed", "<h2 style='color:#1e293b;font-size:18px;margin-top:24px;'>💬 Topics Discussed</h2>")
    html_body = html_body.replace("\n- ", "\n<li style='margin-bottom:6px;'>")
    html_body = html_body.replace("\n", "<br>")

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;padding:32px 24px;color:#334155;">
      <div style="text-align:center;margin-bottom:32px;">
        <h1 style="font-size:20px;font-weight:700;color:#0f172a;margin-bottom:4px;">
          Meeting <span style="color:#3b82f6;">Memory</span>
        </h1>
        <p style="font-size:14px;color:#64748b;">Your Weekly Digest</p>
      </div>
      <p style="font-size:15px;color:#334155;margin-bottom:20px;">
        Hi {user_name}, here's your meeting summary for the past week
        ({meeting_count} meeting{"s" if meeting_count != 1 else ""}).
      </p>
      <div style="background:#f8fafc;border-radius:12px;padding:20px;border:1px solid #e2e8f0;">
        {html_body}
      </div>
      <p style="font-size:12px;color:#94a3b8;margin-top:24px;text-align:center;">
        You're receiving this because you have digest emails enabled.
        <a href="#" style="color:#3b82f6;">Unsubscribe</a>
      </p>
    </div>
    """
