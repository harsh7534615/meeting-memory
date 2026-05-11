# Meeting Memory OS — Product Requirements Document (PRD)

**Version:** 1.1
**Author:** Engineering Team
**Date:** May 2026
**Status:** Active

---

## 1. Overview

**Meeting Memory OS** is a SaaS web application that automatically ingests Google Meet transcripts, processes them with AI, and enables users to query their complete meeting history using natural language. It functions as a personal knowledge base for everything discussed across meetings.

## 2. Problem Statement

Knowledge workers attend dozens of meetings every week. Critical decisions, action items, and context are locked inside unstructured transcript files scattered across Google Drive. There is no fast, reliable way to recall what was discussed, who said what, or what decisions were made without manually reading through entire transcripts.

## 3. Target Users

- **Primary:** Individual knowledge workers (engineers, PMs, designers) who attend frequent Google Meet calls and want instant recall of meeting context.
- **Secondary:** Team leads and managers seeking aggregated insights into meeting patterns, team participation, and decision velocity.

## 4. Core Value Proposition

> "Ask anything about your past meetings and get a cited, grounded answer in seconds."

## 5. Functional Requirements

### 5.1 Authentication & Onboarding
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Users sign in via Google OAuth 2.0 | P0 |
| FR-02 | App requests Google Drive read-only scope during OAuth | P0 |
| FR-03 | User profile (name, email, avatar) is stored on first login | P0 |
| FR-04 | OAuth access + refresh tokens are securely stored server-side | P0 |
| FR-05 | All dashboard routes are protected; unauthenticated users redirected to /login | P0 |

### 5.2 Transcript Ingestion (Google Drive → Pipeline)
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10 | System registers a Google Drive push notification webhook per user | P0 |
| FR-11 | Webhook filters events to only process files matching "Meet Transcript" in name, .docx/.txt, in /Meet Recordings/ | P0 |
| FR-12 | Transcript file content is downloaded via Google Drive API | P0 |
| FR-13 | Processing is idempotent: duplicate file IDs are ignored | P0 |
| FR-14 | Webhooks auto-renew before 7-day expiry | P1 |

### 5.3 Transcript Processing Pipeline
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-20 | Transcripts are chunked with speaker-awareness (max 300 words, 2-sentence overlap) | P0 |
| FR-21 | Chunks are embedded using Gemini embedding model (768 dimensions) | P0 |
| FR-22 | Embeddings + metadata stored in Pinecone vector index | P0 |
| FR-23 | Meeting record (title, date, participants, file_id) stored in Postgres | P0 |
| FR-24 | Chunk records stored in Postgres with Pinecone ID cross-reference | P0 |
| FR-25 | AI-generated meeting summary (3-5 bullet points) stored in Postgres | P0 |

### 5.4 RAG Query Engine
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-30 | User submits a natural language question via the UI | P0 |
| FR-31 | Question is embedded → top-K Pinecone results retrieved → confidence gated → re-ranked → grounded answer generated via Gemini | P0 |
| FR-32 | Answer includes inline citations linking to source transcript chunks (speaker, timestamp, meeting title) | P0 |
| FR-33 | Low-confidence queries return a "not enough context" message instead of hallucinating | P0 |
| FR-34 | Filters supported: date range, speaker name | P1 |

### 5.5 Meeting Hub
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-40 | Users can browse all their processed meetings in a grid/list view | P0 |
| FR-41 | Each meeting card shows: title, date, duration, participant count, AI summary preview | P0 |
| FR-42 | Meeting detail view shows: full summary, participants, transcript chunks with speaker colors | P0 |

### 5.6 Team Insights Dashboard
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-50 | Dashboard shows key metrics: total meetings, average duration, unique participants, total chunks processed | P1 |
| FR-51 | Meeting volume chart: weekly meeting counts over the selected period | P1 |
| FR-52 | Participation breakdown: speaker activity ranked by chunk count | P1 |
| FR-53 | Recent activity feed: latest processed meetings | P1 |
| FR-54 | Time period filter: Last 7, 30, 90 days | P2 |

### 5.7 Weekly Digest
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-60 | System generates a weekly email digest summarizing all meetings from the past 7 days | P1 |
| FR-61 | Digest includes: key decisions, action items, open questions, topics covered | P1 |
| FR-62 | Users can toggle digest on/off in Settings | P1 |
| FR-63 | Users can preview the current digest in the app | P2 |

### 5.8 Settings
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-70 | Account info display (name, email, avatar from Google) | P0 |
| FR-71 | Connected services status (Google Drive connection) | P1 |
| FR-72 | Digest email toggle (on/off) | P1 |

## 6. Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-01 | API rate limited at 10 req/min per user on /query | Security |
| NFR-02 | All inputs validated via Pydantic models | Security |
| NFR-03 | OAuth tokens never exposed to frontend | Security |
| NFR-04 | Structured JSON logging on all backend operations | Observability |
| NFR-05 | Query response time < 5 seconds (p95) | Performance |
| NFR-06 | Frontend fully responsive (mobile, tablet, desktop) | Usability |
| NFR-07 | Dark mode UI with high-contrast accessibility | Usability |

## 7. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS v3, shadcn/ui, Lucide Icons |
| Backend | FastAPI (Python 3.11), SQLAlchemy (asyncpg) |
| Auth | Google OAuth 2.0 via NextAuth.js |
| AI / Embeddings | Gemini 2.5 Flash + gemini-embedding-001 (768 dims) |
| Vector DB | Pinecone (serverless, AWS us-east-1, cosine) |
| Relational DB | Supabase (Postgres, Session Pooler for IPv4) |
| Email | Resend |
| Deployment | Vercel (frontend) + Render (backend) |

## 8. Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Next.js UI  │────▶│  FastAPI API  │────▶│  Supabase DB  │
│  (Vercel)    │◀────│  (Render)     │────▶│  (Postgres)   │
└─────────────┘     └──────────────┘     └───────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │ Pinecone │  │ Gemini   │
              │ (Vectors)│  │ (AI/LLM) │
              └──────────┘  └──────────┘
```

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Query accuracy (cited answer matches transcript) | > 85% |
| Query latency (p95) | < 5 seconds |
| Transcript processing success rate | > 99% |
| Weekly active users (post-launch) | Track |
| Digest open rate | > 30% |

## 10. Out of Scope (v1)

- Real-time meeting transcription (we only process post-meeting files)
- Multi-tenant team workspaces with shared meeting pools
- Calendar integration (Google Calendar sync)
- Slack / Teams integrations
- Custom embedding model fine-tuning
- Audio file processing (only text transcripts)

## 11. Release History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Apr 2026 | Initial build: Phases 1-9 (Auth, Drive, Pipeline, RAG, UI, Digest, Hardening, Deploy) |
| 1.1 | May 2026 | UI redesign (dark mode, Superdesign mockups), Team Insights dashboard feature |
