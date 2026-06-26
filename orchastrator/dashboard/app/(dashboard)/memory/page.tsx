'use client';

import { useMemory } from '@/hooks/useMemory';
import { Loading } from '@/components/common/Loading';
import { Error as ErrorView } from '@/components/common/Error';

function typeStyle(type: string) {
  switch (type) {
    case 'long_term':  return 'text-violet-400 border-violet-700/50 bg-violet-900/20';
    case 'episodic':    return 'text-cyan-400 border-cyan-700/50 bg-cyan-900/20';
    case 'semantic':    return 'text-emerald-400 border-emerald-700/50 bg-emerald-900/20';
    case 'working':     return 'text-orange-400 border-orange-700/50 bg-orange-900/20';
    default:            return 'text-zinc-400 border-zinc-700 bg-zinc-800/50'; // short_term
  }
}

export default function MemoryPage() {
  const { memories, loading, error, refetch } = useMemory();

  if (loading) return <Loading />;
  if (error) return <ErrorView message={error} onRetry={refetch} />;

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-4">
      <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Memory_Lake</span>

      {memories.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <span className="text-[11px] tracking-widest text-zinc-600 uppercase">No memory entries yet</span>
        </div>
      ) : (
        <div className="flex flex-col gap-2 overflow-y-auto">
          {memories.map((entry) => (
            <div key={entry.id} className="rounded border border-zinc-800 bg-zinc-900/50 p-3.5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold text-zinc-200">{entry.key}</span>
                <span className={`text-[9px] font-bold tracking-widest border rounded px-1.5 py-0.5 uppercase ${typeStyle(entry.memory_type)}`}>
                  {entry.memory_type}
                </span>
              </div>
              <pre className="text-[10px] text-zinc-500 leading-relaxed whitespace-pre-wrap break-words">
                {typeof entry.value === 'string' ? entry.value : JSON.stringify(entry.value, null, 2)}
              </pre>
              <div className="text-[9px] text-zinc-600 tracking-wider mt-2">
                {new Date(entry.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
