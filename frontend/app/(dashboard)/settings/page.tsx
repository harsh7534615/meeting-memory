"use client";

import { useSession } from "next-auth/react";
import { useState } from "react";

export default function SettingsPage() {
  const { data: session } = useSession();
  const [digestEnabled, setDigestEnabled] = useState(true);

  const initials = session?.user?.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() ?? "?";

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <h1 className="mb-1 text-xl font-bold text-slate-900">Settings</h1>
      <p className="mb-8 text-sm text-slate-500">
        Manage your account and preferences
      </p>

      {/* Account */}
      <Section title="Account">
        <Card>
          <div className="flex items-center gap-3.5">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-slate-100 text-lg font-semibold text-slate-500">
              {initials}
            </div>
            <div>
              <div className="font-semibold text-slate-900">
                {session?.user?.name ?? "User"}
              </div>
              <div className="text-sm text-slate-500">
                {session?.user?.email ?? ""}
              </div>
            </div>
          </div>
        </Card>
      </Section>

      {/* Connected Services */}
      <Section title="Connected Services">
        <Card>
          <StatusRow label="Google Account" value={<Badge color="green">Connected</Badge>} />
          <StatusRow label="Google Drive Access" value={<Badge color="green">Read-only</Badge>} />
          <StatusRow label="Drive Webhook" value={<Badge color="green">Active</Badge>} />
          <StatusRow label="Meetings Processed" value={<span className="text-sm text-slate-500">—</span>} last />
        </Card>
      </Section>

      {/* Preferences */}
      <Section title="Preferences">
        <Card>
          <div className="flex items-center justify-between py-3.5">
            <div>
              <div className="text-sm text-slate-800">Weekly Digest Email</div>
              <div className="text-xs text-slate-400">
                Receive a summary of decisions and action items every Monday
              </div>
            </div>
            <button
              onClick={() => setDigestEnabled(!digestEnabled)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                digestEnabled ? "bg-blue-500" : "bg-slate-300"
              }`}
            >
              <span
                className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
                  digestEnabled ? "left-[22px]" : "left-0.5"
                }`}
              />
            </button>
          </div>
        </Card>
      </Section>

      {/* Danger */}
      <Section title="Danger Zone">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-slate-800">
                Disconnect Google Account
              </div>
              <div className="text-xs text-slate-400">
                This will remove all your data and stop watching for new
                transcripts.
              </div>
            </div>
            <button className="rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50">
              Disconnect
            </button>
          </div>
        </Card>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <div className="mb-3 text-sm font-semibold text-slate-800">{title}</div>
      {children}
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      {children}
    </div>
  );
}

function StatusRow({
  label,
  value,
  last,
}: {
  label: string;
  value: React.ReactNode;
  last?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between py-3.5 ${
        last ? "" : "border-b border-slate-100"
      }`}
    >
      <span className="text-sm text-slate-600">{label}</span>
      {value}
    </div>
  );
}

function Badge({
  color,
  children,
}: {
  color: "green" | "yellow" | "red";
  children: React.ReactNode;
}) {
  const colors = {
    green: "bg-green-50 text-green-600",
    yellow: "bg-yellow-50 text-yellow-600",
    red: "bg-red-50 text-red-600",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${colors[color]}`}>
      {children}
    </span>
  );
}
