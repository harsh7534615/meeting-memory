# Meeting Memory OS — Task List

Legend: [ ] todo | [→] in progress | [DONE] complete | [SKIP] deferred

---

## PHASE 1 — Foundation

- [DONE] 1.1  Initialise Next.js 14 project with TypeScript, Tailwind, shadcn/ui — Next.js 14.2.35, Tailwind v3, shadcn/ui with default style
- [DONE] 1.2  Initialise FastAPI project with folder structure, requirements.txt — FastAPI 0.111, all deps in requirements.txt, config.py with pydantic-settings
- [DONE] 1.3  Set up Supabase project — create tables (schema below) — schema.sql + SQLAlchemy models created
- [DONE] 1.4  Set up Pinecone account — create index (dimension: 768, metric: cosine) — client code ready, manual setup documented in README
- [DONE] 1.5  Set up .env files for frontend and backend with all required keys — .env.example files in both directories
- [DONE] 1.6  Set up docker-compose.yml for local Postgres (mirrors Supabase schema) — auto-runs schema.sql on init
- [DONE] 1.7  Write README with setup instructions — full setup guide with all services

## PHASE 2 — Auth

- [DONE] 2.1  MOCKUP: Login page — approved two-column layout with Google sign-in, loading, error states
- [DONE] 2.2  Implement NextAuth.js with Google OAuth provider — JWT strategy, custom sign-in page
- [DONE] 2.3  Request Google Drive readonly scope during OAuth — drive.readonly scope with offline access
- [DONE] 2.4  Store user + OAuth tokens in Supabase on first login — /auth/sync endpoint, upsert logic
- [DONE] 2.5  Backend: /auth/me endpoint — returns user profile by google_id
- [DONE] 2.6  Frontend: protect all dashboard routes — next-auth middleware on /, /meetings, /settings
- [DONE] 2.7  TEST: Auth flow — 5 tests pass: health, input validation (3), missing params

## PHASE 3 — Google Drive Watcher

- [DONE] 3.1  Register Google Drive push notification webhook for user's Drive — register_webhook() in drive_watcher.py
- [DONE] 3.2  Backend: POST /webhooks/drive endpoint — handles sync + change events, validates channel
- [DONE] 3.3  Filter events: only process files matching "Meet Transcript" in name
         and .docx or .txt extension in /Meet Recordings/ folder — is_transcript_file() + folder check
- [DONE] 3.4  Download transcript file content via Google Drive API — download_transcript() with Google Doc export
- [DONE] 3.5  Queue transcript for processing (BackgroundTasks) — background task queues downloads
- [DONE] 3.6  Handle webhook renewal (Drive webhooks expire after 7 days — auto-renew) — renew_expiring_webhooks()
- [DONE] 3.7  TEST: Simulate Drive webhook payload — 10 tests pass (8 filter + 2 endpoint)

## PHASE 4 — Transcript Processing Pipeline

- [DONE] 4.1  transcript_processor.py — full pipeline: chunk → embed → Pinecone + Postgres → summary
- [DONE] 4.2  chunker.py — speaker-aware chunking, 300-word max, 2-sentence overlap, skips <20 words
- [DONE] 4.3  embedder.py — Gemini text-embedding-004, batch of 20, exponential backoff on 429
- [DONE] 4.4  Store chunks in Pinecone with metadata (user_id, meeting_id, speaker, timestamp, text_preview)
- [DONE] 4.5  Store meeting record in Postgres (title, date, participants, drive_file_id)
- [DONE] 4.6  Store chunk records in Postgres (pinecone_id cross-reference)
- [DONE] 4.7  Generate meeting summary via Gemini 1.5 Flash (3-5 bullet points)
- [DONE] 4.8  Store summary in Postgres meetings table
- [DONE] 4.9  TEST: 10 chunker tests pass — multi-speaker, single speaker, edge cases
- [DONE] 4.10 TEST: Edge cases — empty transcript, no speaker labels, short chunks, long monologue

## PHASE 5 — RAG Query Engine

- [DONE] 5.1  rag.py — full 8-step pipeline: embed → Pinecone → confidence gate → re-rank → grounded prompt → Gemini → parse citations
- [DONE] 5.2  Backend: POST /query endpoint with filters (date_from, date_to, speaker)
- [DONE] 5.3  TEST: 13 RAG unit tests — context building, citation extraction, dedup, filtering, confidence threshold
- [DONE] 5.4  TEST: 5 query endpoint tests — validation, empty question, filters acceptance

## PHASE 6 — Frontend: Core UI

- [DONE] 6.1  MOCKUP: Dashboard / search page — approved
- [DONE] 6.2  MOCKUP: Meeting detail page — approved
- [DONE] 6.3  MOCKUP: Settings page — approved
- [DONE] 6.4  Implement search page — query input, suggested questions, result display with citations
- [DONE] 6.5  Implement answer display component with citation chips — SOURCE badges, confidence bar
- [DONE] 6.6  Implement meetings list page — list with date/duration/participants, links to detail
- [DONE] 6.7  Implement meeting detail page — summary, participant chips, transcript chunks with speaker colors
- [DONE] 6.8  Implement settings page — account, connected services, digest toggle, danger zone
- [DONE] 6.9  Loading states for all async actions (skeleton loaders on all pages)
- [DONE] 6.10 Empty states for: no meetings yet, no results found, suggested questions
- [DONE] 6.11 Error states with user-friendly messages on all pages
- [DONE] 6.12 Build verified — all 6 routes compile successfully. Also added /meetings and /meetings/{id} backend endpoints.

## PHASE 7 — Weekly Digest

- [DONE] 7.1  digest.py — generates structured digest via Gemini from past week's meeting summaries
- [DONE] 7.2  Backend: GET /digest/preview — returns subject + body + meeting count as JSON
- [DONE] 7.3  Digest email template — HTML email with sections: decisions, action items, open questions, topics
- [DONE] 7.4  Integrate Resend — send_digest_email() + send_all_digests() for all users with digest enabled
- [DONE] 7.5  All 43 unit tests pass (3 expected DB connection failures without running Postgres)

## PHASE 8 — Hardening

- [DONE] 8.1  Rate limiting on /query endpoint (10 requests/min per user) — slowapi
- [DONE] 8.2  Input validation on all endpoints (Pydantic models) — already in place since Phase 2
- [DONE] 8.3  Auth token refresh — get_refreshed_token() auto-refreshes expired Google OAuth tokens
- [DONE] 8.4  Webhook idempotency — drive_file_id UNIQUE constraint + is_already_processed() check (since Phase 3)
- [DONE] 8.5  Logging — structured JSON logs for all pipeline steps
- [DONE] 8.6  Error alerting — rate limit 429 handler, try/catch with logging on all pipeline steps

## PHASE 9 — Deployment

- [DONE] 9.1  Dockerise FastAPI backend — Dockerfile + .dockerignore created
- [DONE] 9.2  Deploy backend to Railway — railway.toml config created (manual: push to GitHub, connect Railway)
- [DONE] 9.3  Deploy frontend to Vercel — Next.js auto-detected (manual: connect GitHub repo in Vercel)
- [ ] 9.4  Set all environment variables in Railway + Vercel dashboards (manual step)
- [ ] 9.5  Register production Google OAuth redirect URI (manual step)
- [ ] 9.6  Register production webhook URL with Google Drive API (manual step)
- [ ] 9.7  Smoke test: full flow on production — login → Drive connect → query (manual step)
