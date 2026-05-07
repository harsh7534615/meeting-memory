# Meeting Memory OS — API Contract

> Auto-generated from FastAPI. This file will be populated when the backend is initialized.

## Base URL

- Local: `http://localhost:8000`
- Production: TBD

## Endpoints

### Auth
- `GET /auth/me` — Return current user profile (requires valid session)

### Query
- `POST /query` — Submit a natural language question against meeting history

### Meetings
- `GET /meetings` — List all meetings for the authenticated user
- `GET /meetings/{id}` — Get meeting detail with summary and chunks

### Webhooks
- `POST /webhooks/drive` — Receive Google Drive push notification events

### Digest
- `GET /digest/preview` — Preview this week's digest for the authenticated user
