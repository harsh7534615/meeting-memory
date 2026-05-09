"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { apiGet } from "@/lib/api-client";
import type { Meeting } from "@/lib/types";

export default function MeetingsPage() {
  const { data: session } = useSession();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session?.googleId) return;
    apiGet<Meeting[]>(`/meetings?google_id=${session.googleId}`)
      .then(setMeetings)
      .catch(() => setError("Failed to load meetings."))
      .finally(() => setLoading(false));
  }, [session?.googleId]);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <h1 className="mb-1 text-xl font-bold text-slate-900">Meetings</h1>
      <p className="mb-6 text-sm text-slate-500">
        All your processed meeting transcripts
      </p>

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="h-4 w-3/5 animate-pulse rounded bg-slate-100" />
              <div className="mt-2 h-3 w-2/5 animate-pulse rounded bg-slate-100" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Empty */}
      {!loading && !error && meetings.length === 0 && (
        <div className="flex flex-col items-center py-20 text-center">
          <div className="mb-4 text-5xl">📋</div>
          <h3 className="mb-2 text-lg font-semibold text-slate-800">
            No meetings yet
          </h3>
          <p className="max-w-sm text-sm text-slate-500">
            Once your Google Meet transcripts are processed, they&apos;ll appear
            here. Make sure your Google Drive is connected in Settings.
          </p>
        </div>
      )}

      {/* List */}
      {!loading && meetings.length > 0 && (
        <div className="space-y-3">
          {meetings.map((m) => (
            <Link
              key={m.id}
              href={`/meetings/${m.id}`}
              className="block rounded-xl border border-slate-200 bg-white p-5 transition-colors hover:border-slate-300 hover:shadow-sm"
            >
              <div className="mb-1 font-semibold text-slate-900">
                {m.title || "Untitled Meeting"}
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-slate-400">
                <span>📅 {m.meeting_date}</span>
                {m.duration_minutes && <span>⏱ {m.duration_minutes} min</span>}
                {m.participant_names?.length > 0 && (
                  <span>👥 {m.participant_names.length} participants</span>
                )}
              </div>
              {m.summary && (
                <p className="mt-2 line-clamp-2 text-sm text-slate-500">
                  {m.summary}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
