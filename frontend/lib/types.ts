import "next-auth";

declare module "next-auth" {
  interface Session {
    accessToken: string;
    googleId: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    googleId?: string;
  }
}

// --- App types ---

export interface Citation {
  source_index: number;
  meeting_title: string;
  meeting_date: string;
  speaker: string;
  timestamp: string;
  text_preview: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
}

export interface Meeting {
  id: string;
  title: string;
  meeting_date: string;
  duration_minutes: number | null;
  summary: string | null;
  participant_names: string[];
  processed_at: string;
}

export interface ChunkInfo {
  id: string;
  speaker: string;
  start_time: string;
  end_time: string;
  text_preview: string;
  chunk_index: number;
}

export interface MeetingDetail extends Meeting {
  chunks: ChunkInfo[];
}

export interface UserProfile {
  id: string;
  google_id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  timezone: string;
  digest_enabled: boolean;
}
