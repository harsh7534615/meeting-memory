# Meeting Memory OS

> Query your entire meeting history in natural language. Powered by Google Meet transcripts and Gemini AI.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.11) |
| Auth | Google OAuth 2.0 (via NextAuth.js) |
| AI / Embeddings | Gemini 1.5 Flash + text-embedding-004 |
| Vector DB | Pinecone |
| Relational DB | Supabase (Postgres) |
| Email | Resend |
| Deployment | Vercel (frontend) + Railway (backend) |

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (for local Postgres)
- Google Cloud project with OAuth 2.0 credentials
- Supabase account (free tier)
- Pinecone account (free tier)
- Gemini API key (free tier)
- Resend account (free tier)

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd meeting-memory
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local
# Fill in your Google OAuth credentials and API URL
npm install
npm run dev
```

### 3. Backend

```bash
cd backend
cp .env.example .env
# Fill in all API keys and credentials

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Database (local dev)

```bash
# From project root
docker compose up -d
```

This starts a local Postgres on port 5432 and runs the schema automatically.

### 5. Supabase (production)

1. Create a new Supabase project
2. Go to SQL Editor → paste contents of `backend/app/database/schema.sql`
3. Copy the project URL and service key to `backend/.env`

### 6. Pinecone

1. Create a free Pinecone account
2. Create an index:
   - **Name:** `meeting-memory`
   - **Dimensions:** `768`
   - **Metric:** `cosine`
3. Copy the API key to `backend/.env`

### 7. Google Cloud

1. Create a project in Google Cloud Console
2. Enable Google Drive API
3. Create OAuth 2.0 credentials (Web application)
4. Add redirect URIs:
   - `http://localhost:3000/api/auth/callback/google` (dev)
   - `http://localhost:8000/auth/callback` (backend dev)
5. Copy client ID and secret to both `.env` files

## Documentation

- [Task List](docs/TASKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Contract](docs/API.md)
