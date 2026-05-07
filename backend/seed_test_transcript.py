"""
Test script: Simulate a transcript going through the full pipeline.
Run with: python seed_test_transcript.py
"""
import asyncio
import sys

# Sample transcript from a realistic sprint planning meeting
SAMPLE_TRANSCRIPT = """Alice 00:00:05
Good morning everyone. Let's start with the sprint review. We had a productive week and I want to go through the highlights before we plan the next sprint.

Bob 00:01:30
Thanks Alice. The auth system is now complete. We implemented Google OAuth with drive readonly scope using NextAuth.js. The login page is live with a two-column layout and all tests are passing. Users can sign in and we store their tokens securely.

Alice 00:02:45
Great work Bob. What about the database migration? Did we get that sorted out with the new schema?

Bob 00:03:15
Yes, the schema is deployed to Supabase. All five tables are created with proper indexes. We have users, oauth tokens, drive webhooks, meetings, and chunks tables. The SQLAlchemy models mirror everything perfectly.

Carol 00:04:00
I finished the Drive watcher integration. Webhooks are registered per user and we filter for Meet Transcript files automatically. The auto-renewal logic handles the 7-day expiry so webhooks never go stale. When a new transcript appears in someone's Drive, we pick it up within seconds.

Alice 00:05:30
Excellent. Let's discuss the RAG pipeline next. We need to decide on the chunk size and overlap strategy before we start building the query engine.

Bob 00:06:00
I suggest 300 words max per chunk with 2-sentence overlap between consecutive chunks. That gives us good context without too much noise in the vector embeddings. We should also skip very short chunks under 20 words.

Carol 00:06:45
Agreed on the chunking strategy. For the embeddings, we should use Gemini text-embedding-004 which gives us 768-dimensional vectors. We can batch embed in groups of 20 to stay within rate limits and add exponential backoff for 429 errors.

Alice 00:07:15
Makes sense. Let's go with that approach. Bob, can you implement the chunker and embedder by end of day? Carol, can you start on the Pinecone integration?

Bob 00:07:30
Yes, I'll have the chunker ready with full test coverage. I'll make sure it handles edge cases like single-speaker transcripts and empty files.

Carol 00:07:45
I'll set up the Pinecone index and write the upsert logic. We decided on cosine similarity metric with 768 dimensions. The metadata will include user ID, meeting ID, speaker, and timestamp for filtering.

Alice 00:08:30
Perfect. Now let's talk about the Q2 budget. We got approval for fifty thousand dollars for infrastructure upgrades. I want to allocate twenty thousand to scaling our compute resources and the rest to monitoring and observability tooling.

Dave 00:09:15
That sounds reasonable. For monitoring, I'd recommend we look at structured JSON logging first since it's free, then add Datadog or similar if we need more. We should also set up rate limiting on the query endpoint to prevent abuse.

Alice 00:10:00
Good point Dave. Let's cap the query endpoint at 10 requests per minute per user. That should be plenty for normal usage while protecting us from runaway scripts.

Bob 00:10:30
I can add that with slowapi. It integrates well with FastAPI and supports per-user rate limiting out of the box. I'll also add input validation with Pydantic models on all endpoints.

Alice 00:11:00
Great. One more thing - the weekly digest feature. Carol, what's the plan there?

Carol 00:11:20
The digest will compile all meetings from the past seven days. It pulls summaries, extracts decisions, action items, and open questions. Then we use Gemini to generate a structured digest and send it via Resend every Monday morning. Users can toggle it on or off in settings.

Alice 00:12:00
Sounds good. Let's wrap up. Action items: Bob handles chunker and rate limiting, Carol handles Pinecone and digest, Dave sets up monitoring. Next standup is Wednesday. Meeting adjourned.

Dave 00:12:30
Thanks everyone. Good meeting.

Bob 00:12:35
See you Wednesday.

Carol 00:12:38
Bye all.
"""


async def main():
    # Import after setting up path
    from app.database.postgres import async_session
    from app.database.models import User
    from app.services.transcript_processor import process_transcript
    from sqlalchemy import select

    async with async_session() as db:
        # Find the user (you should already be logged in)
        result = await db.execute(select(User))
        user = result.scalar_one_or_none()

        if not user:
            print("ERROR: No user found in database. Please log in via the web app first.")
            sys.exit(1)

        print(f"Found user: {user.name} ({user.email})")
        print(f"User ID: {user.id}")
        print()
        print("Processing sample transcript...")
        print("  1. Chunking transcript...")
        print("  2. Embedding chunks via Gemini...")
        print("  3. Storing in Pinecone...")
        print("  4. Storing in Postgres...")
        print("  5. Generating AI summary...")
        print()

        meeting_id = await process_transcript(
            user_id=str(user.id),
            drive_file_id="test-transcript-001",
            file_name="Meet Transcript - Sprint Planning Week 18 2026-05-05.txt",
            content=SAMPLE_TRANSCRIPT,
            db=db,
        )

        if meeting_id:
            print(f"SUCCESS! Meeting processed.")
            print(f"  Meeting ID: {meeting_id}")
            print()
            print("You can now:")
            print("  1. Go to http://localhost:3000 and search for anything discussed")
            print("  2. Try: 'What did we decide about the auth system?'")
            print("  3. Try: 'What's the Q2 budget?'")
            print("  4. Try: 'What are Bob's action items?'")
            print("  5. Check the Meetings page to see the processed meeting")
        else:
            print("ERROR: Processing returned no meeting ID. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
