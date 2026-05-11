# Meeting Memory OS

> Query your entire meeting history in natural language. Powered by Google Meet transcripts and Gemini AI.

**What it does:** Automatically ingests Google Meet transcripts from your Drive, processes them with AI, and lets you ask questions like *"What did we decide about the auth system in last week's sprint?"* — and get a cited, grounded answer with links to exact speakers and timestamps.

## Features

- **Google OAuth login** with automatic Drive access
- **Auto-ingestion** of Meet transcripts via Drive webhooks
- **RAG search** — ask natural language questions, get cited answers
- **Meeting detail** — view transcript chunks, AI summary, participants
- **Weekly digest** — email summary of decisions, action items, open questions
- **Rate limiting, idempotency, structured logging** — production-ready

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.11) |
| Auth | Google OAuth 2.0 (via NextAuth.js) |
| AI / Embeddings | Gemini 2.5 Flash + gemini-embedding-001 |
| Vector DB | Pinecone (serverless, 768 dims, cosine) |
| Relational DB | Supabase (Postgres) |
| Email | Resend |
| Deployment | Vercel (frontend) + Render (backend) |

## Prerequisites

- Node.js 18+
- Python 3.11+
- Accounts (all free tier): **Google Cloud**, **Supabase**, **Pinecone**, **Gemini AI**
- Optional: Docker (only if you want local Postgres instead of Supabase)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/harsh7534615/meeting-memory.git
cd meeting-memory
```

### 2. Google Cloud (required for login)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create a project
2. Enable **Google Drive API**
3. Go to **APIs & Services → Credentials → Create OAuth 2.0 Client ID** (Web application)
4. Add redirect URI: `http://localhost:3000/api/auth/callback/google`
5. Go to **Audience** → add your email as a **test user**
6. Copy the **Client ID** and **Client Secret**

### 3. Gemini API key (required for search + embeddings)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create an API key (free)

### 4. Supabase (required for database)

1. Go to [supabase.com](https://supabase.com) → create a project
2. Go to **SQL Editor** → paste contents of `backend/app/database/schema.sql` → Run (choose "Run without RLS")
3. Go to **Settings → Database** → copy the **Session Pooler** connection string (not Direct)

### 5. Pinecone (required for vector search)

1. Go to [app.pinecone.io](https://app.pinecone.io) → create account
2. Create index: name=`meeting-memory`, dimensions=`768`, metric=`cosine`, serverless, AWS
3. Copy the API key

### 6. Configure environment files

**Frontend** — create `frontend/.env.local`:
```
NEXTAUTH_SECRET=any-random-secret-string
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend** — create `backend/.env`:
```
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GEMINI_API_KEY=<your-gemini-key>
PINECONE_API_KEY=<your-pinecone-key>
PINECONE_INDEX_NAME=meeting-memory
SUPABASE_URL=postgresql+asyncpg://<your-pooler-connection-string>
RESEND_API_KEY=
WEBHOOK_BASE_URL=http://localhost:8000
```

> **Note:** The Supabase URL must start with `postgresql+asyncpg://` (replace `postgresql://` from the Supabase dashboard).

### 7. Install & run

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — sign in with Google and you're in.

### 8. Test with sample data (optional)

To test the full pipeline without a real Google Meet transcript:

```bash
cd backend
python seed_test_transcript.py
```

This injects a sample meeting transcript → chunks it → embeds it → stores in Pinecone + Postgres. Then go to the app and try searching: *"What did we decide about the auth system?"*

## Project Structure

```
meeting-memory/
├── frontend/          # Next.js 14 app (login, search, meetings, settings)
├── backend/           # FastAPI app (auth, query, webhooks, processing pipeline)
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic (chunker, embedder, RAG, digest)
│   │   ├── database/  # Postgres + Pinecone clients, models, schema
│   │   └── tests/     # 43 unit tests
│   └── requirements.txt
├── docs/              # Architecture, task list, API contract, mockups
└── docker-compose.yml # Optional local Postgres
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — system design, data flow, design decisions
- [Task List](docs/TASKS.md) — all 57 tasks across 9 phases (all complete)
- [API Contract](docs/API.md) — endpoint reference
