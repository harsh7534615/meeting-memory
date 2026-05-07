# Meeting Memory OS — Architecture

## Overview

Meeting Memory OS is a SaaS application that ingests Google Meet transcripts, processes them through a RAG (Retrieval-Augmented Generation) pipeline, and enables natural language queries over a user's entire meeting history. The system is split into a Next.js frontend and a FastAPI backend, connected by REST APIs.

---

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│  Next.js 14 (App Router) — Tailwind + shadcn/ui                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Login    │  │  Search  │  │ Meetings │  │ Settings │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API calls
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI BACKEND                            │
│                                                                 │
│  Routers:   /auth  /query  /meetings  /webhooks  /digest       │
│                                                                 │
│  Services:                                                      │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Drive Watcher│  │ Chunker  │  │ Embedder │  │ RAG Engine│  │
│  └──────┬───────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│         │               │             │               │         │
│  ┌──────┴───────────────┴─────────────┴───────────────┘         │
│  │  Transcript Processor (orchestrates pipeline)                │
│  └──────────────────────────────────────────────────────────────│
└─────────────┬───────────────────┬───────────────────┬───────────┘
              │                   │                   │
              ▼                   ▼                   ▼
     ┌────────────┐      ┌───────────┐       ┌───────────────┐
     │  Supabase  │      │  Pinecone │       │  Gemini API   │
     │ (Postgres) │      │ (Vectors) │       │ (LLM + Embed) │
     └────────────┘      └───────────┘       └───────────────┘
```

---

## Data Flow

### 1. Transcript Ingestion

```
Google Meet recording finishes
  → Google auto-generates transcript in Drive (/Meet Recordings/)
    → Drive push notification fires webhook to our backend
      → Backend filters: only .docx/.txt files with "Meet Transcript" in name
        → Background task starts processing pipeline:
          1. Download file content via Drive API
          2. Parse and chunk transcript (speaker turns, 300-word max, 2-sentence overlap)
          3. Embed each chunk via Gemini text-embedding-004
          4. Upsert vectors to Pinecone with metadata
          5. Store meeting + chunk records in Postgres
          6. Generate meeting summary via Gemini 1.5 Flash
```

### 2. Query (RAG Pipeline)

```
User types question in search bar
  → Frontend POSTs to /query
    → Backend embeds question via Gemini text-embedding-004
      → Pinecone similarity search (top_k=10, filtered by user_id)
        → Confidence gate: if best score < 0.70, return "not found" response
          → Re-rank via Gemini (score 1-10), keep top 4 chunks
            → Build grounded prompt with [SOURCE N] citations
              → Gemini 1.5 Flash generates cited answer
                → Parse citations, attach meeting metadata from Postgres
                  → Return answer + citations + confidence to frontend
```

### 3. Weekly Digest

```
Scheduled job (Monday 9am, user's timezone)
  → Fetch all meetings from past 7 days for user
    → Compile summaries into structured digest via Gemini
      → Send HTML email via Resend
```

---

## Key Design Decisions

### Dual database strategy (Postgres + Pinecone)
- **Pinecone** stores vector embeddings for fast semantic search. It is the primary retrieval layer for the RAG pipeline.
- **Postgres (Supabase)** stores structured data: users, meetings, chunks (cross-referenced by Pinecone IDs), OAuth tokens, and webhook registrations. It serves as the relational backbone and source of truth for metadata.
- This separation keeps each database doing what it does best. Chunk text previews are stored in Postgres so we can display them without querying Pinecone.

### Chunking with speaker-aware overlap
- Transcripts are split on speaker turns first, then by word count (max 300 words).
- 2-sentence overlap between consecutive chunks prevents context loss at boundaries.
- Chunks under 20 words are discarded (e.g., "Okay", "Got it") to reduce noise in vector search.

### Confidence gating before generation
- If the best Pinecone match scores below 0.70, the system returns a "no clear discussion found" message instead of generating a potentially hallucinated answer. This is critical for user trust.

### Re-ranking step
- Raw Pinecone scores are a rough proxy for relevance. A Gemini re-rank step scores each chunk 1-10 for actual relevance to the question, keeping only the top 4. This significantly improves answer quality at minimal cost (small Gemini call).

### Background processing (not blocking)
- Transcript processing is done in FastAPI `BackgroundTasks` so the webhook endpoint returns immediately. This prevents webhook timeouts from Google Drive.
- Upgrade path: move to Redis Queue (RQ) if volume warrants it.

### Webhook idempotency
- The `meetings.drive_file_id` column has a UNIQUE constraint. If the same file is received twice (Drive can send duplicate notifications), the second insert is rejected. No transcript is ever processed twice.

### Auth token storage
- Google OAuth tokens are stored in the `oauth_tokens` table. Supabase encrypts data at rest. Tokens are refreshed automatically when expired, using the stored `refresh_token`.

---

## Known Tradeoffs

| Decision | Tradeoff |
|---|---|
| Free-tier Pinecone (1 index) | Single index for all users — must filter by `user_id` on every query. Adequate for early scale. |
| Gemini free tier | Rate-limited. Embedder batches in groups of 20 with exponential backoff on 429s. May need paid tier at scale. |
| BackgroundTasks over Redis Queue | Simpler to start, but tasks are lost if the server restarts mid-processing. Acceptable for MVP; upgrade planned. |
| Server-side RAG only | No client-side caching of embeddings. Every query hits the backend. Fine for now; can add caching later. |
| Single region deployment | Backend on Railway (single region). Latency may be higher for users far from the region. |
| NextAuth.js for auth | Handles OAuth flow on the frontend side. Backend validates tokens independently. Two auth boundaries to maintain. |

---

## Security Considerations

- OAuth tokens are never sent to the frontend. The backend manages all Google API calls.
- All API endpoints require authentication (session validation via `/auth/me`).
- Rate limiting on `/query` (10 req/min per user) prevents abuse.
- Input validation via Pydantic models on all endpoints.
- Webhook endpoint validates Google Drive push notification headers before processing.
- `.env` files are gitignored. `.env.example` files contain only key names, no values.
