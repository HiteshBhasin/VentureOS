'use client';

import { useTasks } from '@/hooks/useTasks';
import { useActiveGoal } from '@/hooks/useActiveGoal';
import { useSystemStream } from '@/hooks/useSystemStream';
import { TaskList } from '@/components/dashboard/TaskList';

// ── helpers ──────────────────────────────────────────────

function formatElapsed(seconds: number) {
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `00:${h}:${m}:${s}`;
}

// ── Page ──────────────────────────────────────────────────

const MOCK_REASONING = [
  { prefix: '>', text: 'INITIALIZING DECOMPOSITION_MODULE...', color: 'text-zinc-500' },
  { prefix: '>', text: 'SCANNING GOAL: "Build a marketing strategy..."', color: 'text-zinc-400' },
  { prefix: '', text: 'DETECTED SECTOR: SaaS (Software as a Service)', color: 'text-cyan-400/70' },
  { prefix: '', text: 'DETECTED REQUIREMENTS:', color: 'text-cyan-400/70' },
  { prefix: '', text: '  Competitor Analysis, Personas, Copy.', color: 'text-cyan-400/60' },
  { prefix: '>', text: 'NODE_A1 COMPLETED: Competitor mapping finalized.', color: 'text-emerald-400/80' },
  { prefix: '>', text: 'INITIATING NODE_B1 (Persona Creation)', color: 'text-zinc-400' },
  { prefix: '', text: 'Thinking: "Based on competitor pricing ($49/mo), user persona likely skews towards mid-market operational managers."', color: 'text-zinc-500 italic' },
  { prefix: '>', text: 'FETCHING PSYCHOGRAPHIC...', color: 'text-cyan-400/50' },
];

export default function TasksPage() {
  const { tasks } = useTasks();
  const { goal } = useActiveGoal();
  const { logs } = useSystemStream();
  
  const displayTasks = tasks.length > 0 ? tasks : [
    { id: 'task-001', title: 'Competitor Analysis', description: 'Scraped top 5 competitors, identified feature gaps and pricing models.', status: 'completed' as const, priority: 'high' as const, progress: 100, tags: ['Node_AI', 'Flow Data'], agent_id: 'mr-001', created_at: '', updated_at: '' },
    { id: 'task-002', title: 'User Persona Creation', description: 'Synthesizing behavioral patterns from competitor analysis to define 3 target archetypes.', status: 'running' as const, priority: 'high' as const, progress: 7, tags: ['Initiating_Decomposit...'], agent_id: 'sl-001', created_at: '', updated_at: '' },
    { id: 'task-003', title: 'Ad Copy Generation', description: 'Waiting for persona completion to generate tailored ad copy variants for LinkedIn and Google.', status: 'queued' as const, priority: 'medium' as const, progress: 0, tags: [], agent_id: null, created_at: '', updated_at: '' },
  ];

  const goalTitle    = goal?.title || '';
  const completion   = goal?.completion || 33; 
  const elapsedSecs  = goal?.elapsed_seconds || 862;

  // Use stream logs as reasoning lines if available, else show mock
  const reasoningLines = logs.length > 0
    ? logs.slice(-9).map((l) => ({ prefix: '>', text: l.message.replace(/^\[.*?\]\s*/, ''), color: 'text-zinc-400' }))
    : MOCK_REASONING;

  // Insight = last log that's meaningful
  const lastLog = logs[logs.length - 1];

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-5 relative">

      {/* Active Goal Header */}
      <div className="flex flex-col gap-3">
        <span className="text-[9px] font-bold tracking-[0.3em] text-cyan-500/70 uppercase border border-cyan-500/20 bg-cyan-500/5 rounded px-2 py-1 w-fit">
          Active_Goal
        </span>
        <h1 className="text-2xl font-bold text-white tracking-tight leading-tight">
          {goalTitle}
        </h1>
        <div className="flex items-center gap-8">
          <div className="flex flex-col gap-1.5 flex-1 max-w-xs">
            <div className="flex items-center justify-between">
              <span className="text-[9px] tracking-widest text-zinc-600 uppercase">Completion</span>
              <span className="text-[9px] tracking-widest text-zinc-400 font-bold">{completion}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-700 to-cyan-400"
                style={{ width: `${completion}%` }}
              />
            </div>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[9px] tracking-widest text-zinc-600 uppercase">Elapsed_Time</span>
            <span className="text-sm font-bold text-zinc-300 tabular-nums tracking-wider">{formatElapsed(elapsedSecs)}</span>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-zinc-800" />

      {/* Two-column layout */}
      <div className="flex gap-4 flex-1 min-h-0">

        {/* Left — Decomposition Flow */}
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Decomposition_Flow</span>
            <div className="flex items-center gap-1.5">
              <button aria-label="Expand flow" className="text-zinc-600 hover:text-zinc-400 transition-colors p-1">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
            </div>
          </div>
          <div className="overflow-y-auto flex-1">
            <TaskList tasks={displayTasks} />
          </div>
        </div>

        {/* Right — Reasoning Engine */}
        <div className="flex flex-col w-72 shrink-0 rounded border border-zinc-800 bg-zinc-900/50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
              <span className="h-2.5 w-2.5 rounded-full bg-yellow-500" />
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            </div>
            <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Reasoning_Engine</span>
            <div className="w-16" />
          </div>
          <div className="flex flex-col flex-1 overflow-y-auto p-4 gap-1.5">
            {reasoningLines.map((line, i) => (
              <div key={i} className="text-[10px] leading-relaxed">
                <span className={`${line.color} break-words`}>
                  {line.prefix && <span className="text-cyan-600 mr-1">{line.prefix}</span>}
                  {line.text}
                </span>
              </div>
            ))}
            <div className="animate-pulse h-3 w-1.5 bg-zinc-600 mt-0.5" />
          </div>
        </div>
      </div>

      {/* New Insight notification */}
      <div className="absolute bottom-5 right-5 flex items-start gap-2.5 rounded border border-cyan-500/30 bg-[#080c18] shadow-lg shadow-cyan-900/20 p-3 max-w-xs">
        <div className="h-5 w-5 shrink-0 rounded-full bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center mt-0.5">
          <svg className="h-2.5 w-2.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-[9px] font-bold tracking-widest text-cyan-400 uppercase mb-1">New Insight</div>
          <p className="text-[10px] text-zinc-400 leading-relaxed">
            {lastLog
              ? lastLog.message.replace(/^\[.*?\]\s*/, '')
              : 'Agent has identified a high-conversion keyword \u201cAutomated Workflow\u201d from competitor analysis.'}
          </p>
        </div>
        <button aria-label="Dismiss insight" className="text-zinc-600 hover:text-zinc-400 transition-colors shrink-0 mt-0.5">
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

    </div>
  );
}
