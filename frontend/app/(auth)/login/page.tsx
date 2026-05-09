"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSignIn() {
    setLoading(true);
    setError(null);
    try {
      await signIn("google", { callbackUrl: "/" });
    } catch {
      setError("Authentication failed. Please try again or check that pop-ups are not blocked.");
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left: Branding */}
      <div className="hidden md:flex flex-1 flex-col justify-center bg-gradient-to-br from-slate-900 to-slate-800 px-16 text-white">
        <h1 className="text-4xl font-bold leading-tight mb-4">
          Never lose a meeting insight again.
        </h1>
        <p className="text-lg text-slate-400 max-w-md leading-relaxed">
          Meeting Memory OS watches your Google Meet transcripts and lets you
          search every conversation in plain English.
        </p>
        <ul className="mt-10 space-y-4">
          {[
            "Auto-ingests transcripts from Google Drive",
            'Ask questions like "What did we decide about auth in March?"',
            "Get cited answers with exact meeting timestamps",
            "Weekly digest of decisions, action items, and topics",
          ].map((feature) => (
            <li
              key={feature}
              className="flex items-center gap-3 text-sm text-slate-300"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-xs text-blue-400">
                ✓
              </span>
              {feature}
            </li>
          ))}
        </ul>
      </div>

      {/* Right: Login */}
      <div className="flex flex-1 flex-col items-center justify-center bg-white px-6 py-16 md:px-12">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-bold mb-1">
            Meeting <span className="text-blue-500">Memory</span>
          </h2>
          <p className="text-sm text-slate-500 mb-10">
            Sign in to search your meeting history
          </p>

          <button
            onClick={handleSignIn}
            disabled={loading}
            className="flex w-full items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white px-6 py-3.5 text-sm font-medium text-slate-800 transition-all hover:bg-slate-50 hover:border-slate-300 hover:shadow-sm disabled:opacity-70 disabled:pointer-events-none"
          >
            {loading ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-blue-500" />
                Signing in...
              </>
            ) : (
              <>
                <svg className="h-5 w-5" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Continue with Google
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="my-8 flex items-center gap-4 text-xs text-slate-400">
            <span className="flex-1 border-t border-slate-200" />
            or
            <span className="flex-1 border-t border-slate-200" />
          </div>

          <p className="text-center text-xs text-slate-400 leading-relaxed">
            By signing in, you agree to our Terms of Service and Privacy Policy.
            <br />
            We only request read-only access to your Google Drive transcripts.
          </p>
        </div>
      </div>
    </div>
  );
}
