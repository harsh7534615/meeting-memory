-- Meeting Memory OS — Database Schema
-- Run this in your Supabase SQL Editor or local Postgres

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  google_id TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  timezone TEXT DEFAULT 'UTC',
  digest_enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- OAuth tokens (encrypted at rest in Supabase)
CREATE TABLE oauth_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at TIMESTAMPTZ,
  scope TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Drive webhook registrations
CREATE TABLE drive_webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  channel_id TEXT UNIQUE NOT NULL,
  resource_id TEXT,
  expiry TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meetings
CREATE TABLE meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  title TEXT,
  meeting_date DATE,
  duration_minutes INT,
  drive_file_id TEXT UNIQUE NOT NULL,  -- idempotency key
  summary TEXT,                         -- Gemini-generated bullet summary
  participant_names TEXT[],
  processed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transcript chunks (cross-reference with Pinecone)
CREATE TABLE chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  pinecone_id TEXT UNIQUE NOT NULL,
  speaker TEXT,
  start_time TEXT,   -- e.g. "00:23:41"
  end_time TEXT,
  text_preview TEXT, -- first 200 chars for display
  chunk_index INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_meetings_user ON meetings(user_id);
CREATE INDEX idx_chunks_meeting ON chunks(meeting_id);
CREATE INDEX idx_chunks_user ON chunks(user_id);
