"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Search", icon: "🔍" },
  { href: "/meetings", label: "Meetings", icon: "📋" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();

  const initials = session?.user?.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() ?? "?";

  return (
    <aside className="flex w-64 flex-col border-r border-slate-200 bg-white">
      {/* Logo */}
      <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
        <span className="text-base font-bold">
          Meeting <span className="text-blue-500">Memory</span>
        </span>
      </div>

      {/* Nav */}
      <nav className="space-y-1 p-3">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-colors",
              pathname === item.href
                ? "bg-slate-100 font-semibold text-slate-900"
                : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
            )}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* User footer */}
      <div className="mt-auto border-t border-slate-200 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-500">
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-slate-800">
              {session?.user?.name ?? "User"}
            </div>
            <div className="truncate text-xs text-slate-400">
              {session?.user?.email ?? ""}
            </div>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="text-xs text-slate-400 hover:text-slate-600"
            title="Sign out"
          >
            ↗
          </button>
        </div>
      </div>
    </aside>
  );
}
