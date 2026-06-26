'use client';

import { useState, useCallback } from 'react';
import { useAgents } from '@/hooks/useAgents';
import { useSystemStatus } from '@/hooks/useSystemStatus';
import { useSystemStream } from '@/hooks/useSystemStream';
import { useActiveGoal } from '@/hooks/useActiveGoal';
import { StreamLog } from '@/types/task';
import { createTask } from "@/lib/api";
import { AgentCard } from "@/components/dashboard/AgentCard";

// ── helpers ──────────────────────────────────────────────

function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${h}:${m}:${s}`;
}

function tagStyle(message: string): { tag: string; tagColor: string } {
  if (message.startsWith('[OK]'))    return { tag: 'OK',    tagColor: 'text-emerald-400' };
  if (message.startsWith('[PROC]'))  return { tag: 'PROC',  tagColor: 'text-cyan-400' };
  if (message.startsWith('[SPAWN]')) return { tag: 'SPAWN', tagColor: 'text-violet-400' };
  if (message.startsWith('[...]'))   return { tag: '...',   tagColor: 'text-zinc-500' };
  return { tag: 'INFO', tagColor: 'text-zinc-400' };
}

function parseLog(log: StreamLog) {
  const { tag, tagColor } = tagStyle(log.message);
  const text = log.message.replace(/^\[.*?\]\s*/, '');
  return { time: log.time, tag, tagColor, text };
}

// ── Page ──────────────────────────────────────────────────

export default function DashboardPage() {
  const { agents } = useAgents();
  const { status } = useSystemStatus();
  const { logs } = useSystemStream();
  const { goal } = useActiveGoal();

  const [objective, setObjective] = useState('');
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [execError, setExecError] = useState<string | null>(null);

  const handleExecute = useCallback(async () => {
    const trimmed = objective.trim();
    if (!trimmed) return;
    setExecError(null);
    setSubmitted(trimmed);
    try {
      await createTask({ title: trimmed, description: '', priority: 'medium' });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setExecError(msg);
    }
  }, [objective]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleExecute();
  }, [handleExecute]);

  const handleClear = useCallback(() => {
    setObjective('');
    setSubmitted(null);
  }, []);

  const displayLogs = logs.length > 0 ? logs.map(parseLog) : [
    { time: '14:20:01', tag: 'OK',    tagColor: 'text-emerald-400', text: 'COMMAND RECEIVED: INIT_MARKETING_STRAT_V2' },
    { time: '14:20:02', tag: 'PROC',  tagColor: 'text-cyan-400',    text: 'ANALYZING OBJECTIVE...' },
    { time: '14:20:02', tag: 'PROC',  tagColor: 'text-cyan-400',    text: 'DECOMPOSING GOAL: "SaaS Product Marketing"' },
    { time: '14:20:03', tag: 'SPAWN', tagColor: 'text-violet-400',  text: 'SPAWNING ANALYST_NODE_04... SUCCESS' },
    { time: '14:20:04', tag: 'PROC',  tagColor: 'text-cyan-400',    text: 'RETRIEVING COMPETITOR DATA VIA PERPLEXITY_ENGINE' },
    { time: '14:20:05', tag: 'OK',    tagColor: 'text-emerald-400', text: 'NODE_04: META STRATEGY GEN COMPONENT ACTIVE' },
    { time: '14:20:06', tag: '...',   tagColor: 'text-zinc-500',    text: 'AGGREGATING MARKET SEGMENTS_' },
  ];

  const displayAgents = agents.length > 0 ? agents : [
    { id: 'sl-001', name: 'STRATEGY_LEAD', type: 'research' as const, status: 'active' as const, activity: 'THINKING', progress: 82, description: 'Refining core value propositions and aligning with growth levers...', tokens_per_sec: 1248, cost_estimate: 0.14, model: 'gpt-4o' },
    { id: 'mr-001', name: 'MARKET_RESEARCHER', type: 'research' as const, status: 'active' as const, activity: 'SCRAPING', progress: 34, description: 'Extracting pricing models from 12 tier-1 competitors.', tokens_per_sec: 0, cost_estimate: 0, model: 'gpt-4o' },
  ];


  const pid = goal?.pid || 48821;
  const memUsed = goal?.memory_used_gb || status.memory_used_gb || 2.4;
  const memTotal = goal?.memory_total_gb || status.memory_total_gb || 32;
  const tokensPerSec = status.tokens_per_sec || 1248;
  const costEst = status.cost_estimate ?? 0.14;
  const uptime = formatUptime(status.uptime_seconds || 252);
  const latency = status.latency_ms || 42;

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-4 gap-4">

      {/* Goal Banner */}
      <div className="rounded border border-cyan-500/30 bg-cyan-500/5 px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <svg className="h-4 w-4 text-cyan-400 shrink-0 animate-spin [animation-duration:3s]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <label htmlFor="user-query" className="shrink-0">
            <span className="text-[10px] tracking-widest uppercase text-cyan-400">Enter Objective:</span>
          </label>
          <input
            type="text"
            name="user-query"
            id="user-query"
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={goal?.title || 'Describe your goal...'}
            className="flex-1 min-w-0 bg-transparent text-zinc-200 text-[11px] tracking-wider border-b border-cyan-500/30 focus:border-cyan-400 outline-none py-1 placeholder:text-zinc-600 placeholder:tracking-widest placeholder:uppercase transition-colors"
          />
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleExecute}
            disabled={!objective.trim()}
            className="rounded border border-cyan-500/40 bg-cyan-500/10 text-cyan-400 text-[10px] font-bold tracking-widest px-4 py-2 uppercase hover:bg-cyan-500/20 hover:border-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Execute
          </button>
          <button
            aria-label="Clear objective"
            onClick={handleClear}
            className="text-zinc-500 hover:text-red-400 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Submitted objective feedback */}
      {submitted && !execError && (
        <div className="flex items-center gap-2 px-1 -mt-2">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
          <span className="text-[10px] text-emerald-400 tracking-widest uppercase">OBJECTIVE SET: {submitted}</span>
        </div>
      )}

      {/* Error feedback */}
      {execError && (
        <div className="flex items-center gap-2 px-1 -mt-2">
          <span className="h-1.5 w-1.5 rounded-full bg-red-400 shrink-0" />
          <span className="text-[10px] text-red-400 tracking-widest uppercase truncate" title={execError}>ERROR: {execError}</span>
        </div>
      )}

      {/* PID row */}
      <div className="flex items-center justify-between px-1 -mt-2">
        <span className="text-[10px] text-zinc-600 tracking-widest">PID: {pid} &nbsp; MEMORY: {memUsed}GB / {memTotal}GB</span>
        <span className="text-[10px] text-zinc-600 tracking-widest">{submitted ? `EXECUTING: ${submitted}` : 'Awaiting objective...'}</span>
      </div>

      {/* Main content row */}
      <div className="flex gap-4 flex-1 min-h-0">

        {/* System Stream */}
        <div className="flex flex-col flex-1 rounded border border-zinc-800 bg-zinc-900/50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800">
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-300 uppercase">System Stream</span>
            </div>
            <span className="text-[9px] tracking-widest text-zinc-600 border border-zinc-700 rounded px-1.5 py-0.5">
              {latency.toFixed(3)}ms LATENCY
            </span>
          </div>
          <div className="flex flex-col gap-1.5 p-4 flex-1 overflow-y-auto">
            {displayLogs.map((log, i) => (
              <div key={i} className="flex items-start gap-2 text-[11px] leading-relaxed">
                <span className="text-zinc-600 shrink-0 tabular-nums">{log.time}</span>
                <span className={`shrink-0 font-bold ${log.tagColor}`}>[{log.tag}]</span>
                <span className="text-zinc-400">{log.text}</span>
              </div>
            ))}
            <div className="animate-pulse h-4 w-2 bg-cyan-400/60 mt-1" />
          </div>
          <div className="border-t border-zinc-800 py-2 text-center">
            <button className="text-[9px] text-zinc-600 hover:text-zinc-400 tracking-widest uppercase transition-colors">
              Scroll To Bottom
            </button>
          </div>
        </div>

        {/* Right column — agent cards */}
        <div className="flex flex-col gap-3 w-60 shrink-0">
          {displayAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}

          {/* Stats row */}
          <div className="rounded border border-zinc-800 bg-zinc-900/50 p-3 grid grid-cols-2 gap-2">
            <div>
              <div className="text-[9px] text-zinc-600 tracking-widest uppercase mb-0.5">Tokens/Sec</div>
              <div className="text-lg font-bold text-zinc-200 tracking-tight">{tokensPerSec.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-[9px] text-zinc-600 tracking-widest uppercase mb-0.5">Cost (Est)</div>
              <div className="text-lg font-bold text-zinc-200 tracking-tight">${costEst.toFixed(2)}</div>
            </div>
          </div>

          {/* Spawning placeholder */}
          <div className="rounded border border-dashed border-zinc-800 bg-zinc-900/20 p-3.5 flex flex-col items-center justify-center gap-2 opacity-40">
            <svg className="h-6 w-6 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span className="text-[9px] text-zinc-600 tracking-widest uppercase text-center">Spawning Content_Architect</span>
          </div>
        </div>
      </div>

      {/* Dynamic Task Graph */}
      <div className="rounded border border-zinc-800 bg-zinc-900/50 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800">
          <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-300 uppercase">Dynamic Task Graph</span>
          <div className="flex items-center gap-2">
            <button aria-label="Expand graph" className="text-zinc-600 hover:text-zinc-400 transition-colors">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
          </div>
        </div>
        <div className="relative h-44 p-4 overflow-hidden">
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            <line x1="130" y1="72" x2="255" y2="52" stroke="#334155" strokeWidth="1.5" strokeDasharray="5,4" />
            <line x1="130" y1="80" x2="255" y2="108" stroke="#334155" strokeWidth="1.5" strokeDasharray="5,4" />
          </svg>

          <div className="absolute flex flex-col items-center gap-1.5 left-10 top-[50px]">
            <div className="h-12 w-12 rounded-lg bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center">
              <svg className="h-5 w-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <span className="text-[9px] text-cyan-400 font-bold tracking-widest">CORE_STRAT</span>
          </div>

          <div className="absolute rounded border border-cyan-500/50 bg-cyan-500/10 px-3 py-2 min-w-[140px] left-[260px] top-7">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[10px] font-bold text-cyan-300 tracking-wide">Meta Strategy Gen</span>
            </div>
            <span className="text-[9px] text-cyan-600 tracking-widest uppercase">Status: Generating</span>
          </div>

          <div className="absolute rounded border border-zinc-700 bg-zinc-800/50 px-3 py-2 min-w-[130px] opacity-50 left-[260px] top-24">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
              <span className="text-[10px] font-bold text-zinc-400 tracking-wide">Market Research</span>
            </div>
            <span className="text-[9px] text-zinc-600 tracking-widest uppercase">Idle</span>
          </div>
        </div>
      </div>

      {/* Session footer */}
      <div className="flex justify-end">
        <button className="flex items-center gap-2 rounded border border-zinc-800 bg-zinc-900/50 px-3 py-2 text-[10px] text-zinc-400 hover:bg-zinc-800 transition-colors tracking-widest uppercase">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Current Session &nbsp; Uptime: {uptime}
          <svg className="h-3 w-3 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

    </div>
  );
}
