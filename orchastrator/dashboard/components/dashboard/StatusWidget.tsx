import { Agent } from '@/types/agent';

interface StatusWidgetProps {
  agent: Agent;
}

function statusStyle(status: Agent['status']) {
  switch (status) {
    case 'active':  return 'text-emerald-400 border-emerald-700/50 bg-emerald-900/20';
    case 'error':   return 'text-red-400 border-red-700/50 bg-red-900/20';
    case 'stopped': return 'text-zinc-500 border-zinc-700 bg-zinc-800/50';
    default:        return 'text-zinc-400 border-zinc-700 bg-zinc-800/50';
  }
}

export function StatusWidget({ agent }: StatusWidgetProps): React.JSX.Element {
  return (
    <div className="flex items-center justify-between gap-3 rounded border border-zinc-800 bg-zinc-900/50 px-3 py-2 font-mono">
      <div className="flex items-center gap-2 min-w-0">
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${agent.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
        <span className="text-[10px] font-bold tracking-widest text-zinc-300 truncate">{agent.name}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-[9px] text-zinc-500 tabular-nums">{agent.progress}%</span>
        <span className={`text-[9px] font-bold tracking-widest rounded border px-1.5 py-0.5 uppercase ${statusStyle(agent.status)}`}>
          {agent.status}
        </span>
      </div>
    </div>
  );
}
