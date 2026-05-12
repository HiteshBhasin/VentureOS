"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const tabs = [
  { label: "System", href: "/" },
  { label: "Nodes", href: "/agents" },
  { label: "Network", href: "/tasks" },
];

export function Header() {
  const pathname = usePathname();
  const [query, setQuery] = useState("");

  return (
    <header className="flex items-center justify-between border-b border-zinc-700 bg-zinc-900 px-4 py-2.5">
      {/* Left — search */}
      <div className="flex items-center gap-2 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-1.5 w-56">
        <svg
          className="h-3.5 w-3.5 shrink-0 text-zinc-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
          />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="QUERY_SYSTEM_NODES..."
          className="w-full bg-transparent text-xs font-mono text-zinc-400 placeholder:text-zinc-600 outline-none"
        />
      </div>

      {/* Center — tabs */}
      <nav className="flex items-center gap-1">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-zinc-700 text-white"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>

      {/* Right — status + actions */}
      <div className="flex items-center gap-3">
        {/* Live status badge */}
        <div className="flex items-center gap-1.5 rounded-full border border-emerald-700 bg-emerald-950 px-2.5 py-1">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="text-xs font-semibold uppercase tracking-wide text-emerald-400">
            Live Status
          </span>
        </div>

        {/* Active agents count */}
        <span className="text-xs font-medium text-zinc-400">
          12 Active Agents
        </span>

        {/* Notifications */}
        <button
          aria-label="Notifications"
          className="rounded p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </button>

        {/* Activity */}
        <button
          aria-label="Activity"
          className="rounded p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </button>

        {/* Avatar */}
        <button
          aria-label="Profile"
          className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-700 text-xs font-bold text-zinc-200 hover:bg-zinc-600"
        >
          H
        </button>
      </div>
    </header>
  );
}
