'use client';

import { useSystemStream } from '@/hooks/useSystemStream';

function tagStyle(message: string): { tag: string; tagColor: string } {
  if (message.startsWith('[OK]'))    return { tag: 'OK',    tagColor: 'text-emerald-400' };
  if (message.startsWith('[PROC]'))  return { tag: 'PROC',  tagColor: 'text-cyan-400' };
  if (message.startsWith('[SPAWN]')) return { tag: 'SPAWN', tagColor: 'text-violet-400' };
  if (message.startsWith('[ERROR]') || message.startsWith('✗')) return { tag: 'ERR', tagColor: 'text-red-400' };
  return { tag: 'INFO', tagColor: 'text-zinc-400' };
}

export default function LogsPage() {
  const { logs, connected } = useSystemStream();

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-4">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">System_Logs</span>
        <span className={`flex items-center gap-1.5 text-[9px] tracking-widest uppercase border rounded px-1.5 py-0.5 ${
          connected ? 'text-emerald-400 border-emerald-700/50 bg-emerald-900/20' : 'text-zinc-500 border-zinc-700 bg-zinc-800/50'
        }`}>
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
          {connected ? 'Live' : 'Disconnected'}
        </span>
      </div>

      <div className="flex flex-col flex-1 rounded border border-zinc-800 bg-zinc-900/50 overflow-y-auto p-4 gap-1.5">
        {logs.length === 0 ? (
          <span className="text-[11px] tracking-widest text-zinc-600 uppercase">No logs yet</span>
        ) : (
          logs.map((log, i) => {
            const { tag, tagColor } = tagStyle(log.message);
            const text = log.message.replace(/^\[.*?\]\s*/, '');
            return (
              <div key={i} className="flex items-start gap-2 text-[11px] leading-relaxed">
                <span className="text-zinc-600 shrink-0 tabular-nums">{log.time}</span>
                <span className={`shrink-0 font-bold ${tagColor}`}>[{tag}]</span>
                <span className="text-zinc-400 break-words">{text}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
