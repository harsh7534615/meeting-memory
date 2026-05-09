"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet } from "@/lib/api-client";
import type { MeetingDetail } from "@/lib/types";

export default function MeetingDetailPage() {
  const params = useParams();
  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    apiGet<MeetingDetail>(`/meetings/${params.id}`)
      .then(setMeeting)
      .catch(() => setError("Failed to load meeting."))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="h-4 w-24 animate-pulse rounded bg-slate-100" />
        <div className="mt-6 h-6 w-3/5 animate-pulse rounded bg-slate-100" />
        <div className="mt-3 h-4 w-2/5 animate-pulse rounded bg-slate-100" />
        <div className="mt-8 h-40 animate-pulse rounded-xl bg-slate-100" />
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <Link href="/meetings" className="text-sm text-slate-500 hover:text-blue-500">
          ← Back to meetings
        </Link>
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error || "Meeting not found."}
        </div>
      </div>
    );
  }

  const SPEAKER_COLORS = ["bg-blue-500", "bg-green-500", "bg-amber-500", "bg-purple-500", "bg-rose-500"];

  function speakerColor(speaker: string): string {
    const idx = meeting!.participant_names?.indexOf(speaker) ?? 0;
    return SPEAKER_COLORS[Math.abs(idx) % SPEAKER_COLORS.length];
  }

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <Link href="/meetings" className="mb-5 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-500">
        ← Back to meetings
      </Link>

      {/* Header */}
      <h1 className="mb-2 text-2xl font-bold">{meeting.title || "Untitled Meeting"}</h1>
      <div className="mb-3 flex flex-wrap gap-4 text-sm text-slate-500">
        <span>📅 {meeting.meeting_date}</span>
        {meeting.duration_minutes && <span>⏱ {meeting.duration_minutes} min</span>}
        {meeting.participant_names?.length > 0 && (
          <span>👥 {meeting.participant_names.length} participants</span>
        )}
      </div>
      {meeting.participant_names?.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {meeting.participant_names.map((name) => (
            <span key={name} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              {name}
            </span>
          ))}
        </div>
      )}

      {/* Summary */}
      {meeting.summary && (
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5">
          <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-blue-500">
            AI Summary
          </div>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {meeting.summary}
          </div>
        </div>
      )}

      {/* Transcript chunks */}
      {meeting.chunks?.length > 0 && (
        <>
          <div className="mb-3 text-sm font-semibold text-slate-700">
            Transcript ({meeting.chunks.length} chunks)
          </div>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            {meeting.chunks
              .sort((a, b) => a.chunk_index - b.chunk_index)
              .map((chunk) => (
                <div key={chunk.id} className="border-b border-slate-100 px-5 py-4 last:border-b-0">
                  <div className="mb-1.5 flex items-center gap-2.5">
                    <span className={`h-2 w-2 rounded-full ${speakerColor(chunk.speaker)}`} />
                    <span className="text-sm font-semibold text-slate-800">{chunk.speaker}</span>
                    <span className="text-[11px] text-slate-400">{chunk.start_time}</span>
                  </div>
                  <div className="text-sm leading-relaxed text-slate-600">
                    {chunk.text_preview}
                  </div>
                </div>
              ))}
          </div>
        </>
      )}
    </div>
  );
}
