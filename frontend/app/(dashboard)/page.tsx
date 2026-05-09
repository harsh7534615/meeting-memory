"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { apiPost } from "@/lib/api-client";
import type { QueryResponse, Citation } from "@/lib/types";

const SUGGESTED_QUESTIONS = [
  "What did we decide about the auth system?",
  "What action items came out of last week's sprint?",
  "What did Carol say about the Q2 budget?",
];

export default function SearchPage() {
  const { data: session } = useSession();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(q?: string) {
    const question = q ?? query;
    if (!question.trim()) return;
    setQuery(question);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await apiPost<QueryResponse>("/query", {
        question,
        user_id: session?.googleId ?? "",
      });
      setResult(res);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Search bar */}
      <div className="px-8 pt-6">
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-5 py-3.5 shadow-sm transition-all focus-within:border-blue-500 focus-within:ring-[3px] focus-within:ring-blue-500/10">
          <span className="text-slate-400">🔍</span>
          <input
            type="text"
            className="flex-1 bg-transparent text-[15px] outline-none placeholder:text-slate-400"
            placeholder="Ask anything about your meetings..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button
            onClick={() => handleSearch()}
            disabled={loading}
            className="rounded-lg bg-slate-900 px-5 py-2 text-xs font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {/* Error */}
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-blue-500">
              Searching your meetings...
            </div>
            <div className="space-y-2.5">
              <div className="h-3.5 w-4/5 animate-pulse rounded bg-slate-100" />
              <div className="h-3.5 w-3/5 animate-pulse rounded bg-slate-100" />
              <div className="h-3.5 w-4/5 animate-pulse rounded bg-slate-100" />
              <div className="h-3.5 w-2/5 animate-pulse rounded bg-slate-100" />
            </div>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <>
            <div className="mb-5 rounded-xl border border-slate-200 bg-white p-6">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-blue-500">
                Answer
              </div>
              <div className="whitespace-pre-wrap text-[15px] leading-relaxed text-slate-800">
                {result.answer}
              </div>
              {result.confidence > 0 && (
                <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4">
                  <span className="text-xs text-slate-400">
                    Confidence: {Math.round(result.confidence * 100)}%
                  </span>
                  <div className="h-1 w-24 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-green-500"
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {result.citations.length > 0 && (
              <>
                <div className="mb-2.5 text-xs font-semibold text-slate-500">
                  Sources ({result.citations.length})
                </div>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {result.citations.map((c) => (
                    <CitationCard key={c.source_index} citation={c} />
                  ))}
                </div>
              </>
            )}
          </>
        )}

        {/* Empty state */}
        {!result && !loading && !error && (
          <div className="flex flex-col items-center py-20 text-center">
            <div className="mb-4 text-5xl">💬</div>
            <h3 className="mb-2 text-lg font-semibold text-slate-800">
              Ask about your meetings
            </h3>
            <p className="mb-6 max-w-sm text-sm text-slate-500">
              Type a question in the search bar to find decisions, action items,
              or anything discussed in your meetings.
            </p>
            <div className="flex w-full max-w-sm flex-col gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSearch(q)}
                  className="rounded-lg border border-slate-200 px-4 py-2.5 text-left text-sm text-slate-500 transition-colors hover:border-slate-300 hover:bg-slate-50"
                >
                  &ldquo;{q}&rdquo;
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="cursor-pointer rounded-lg border border-slate-200 bg-slate-50/50 p-3.5 transition-colors hover:border-blue-300 hover:bg-blue-50/30">
      <div className="mb-2 flex items-center justify-between">
        <span className="rounded bg-blue-50 px-2 py-0.5 text-[11px] font-bold text-blue-600">
          SOURCE {citation.source_index}
        </span>
        <span className="text-[11px] text-slate-400">
          {citation.meeting_date}
        </span>
      </div>
      <div className="mb-1 text-xs font-semibold text-slate-800">
        {citation.meeting_title}
      </div>
      <div className="mb-1.5 text-[11px] text-slate-400">
        🎤 {citation.speaker} · ⏱ {citation.timestamp}
      </div>
      <div className="line-clamp-3 text-xs leading-relaxed text-slate-500">
        {citation.text_preview}
      </div>
    </div>
  );
}
