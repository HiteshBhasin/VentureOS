import { Agent } from '@/types/agent';

interface AgentCardProps {
  agent: Agent;
  onClick?: (agent: Agent) => void;
}

function activityColor(activity: string) {
  switch (activity?.toUpperCase()) {
    case 'THINKING':  return 'text-cyan-400';
    case 'SCRAPING':  return 'text-orange-400';
    case 'ANALYZING': return 'text-blue-400';
    case 'WRITING':   return 'text-violet-400';
    default:          return 'text-zinc-400';
  }
}

function barColor(activity: string) {
  switch (activity?.toUpperCase()) {
    case 'THINKING':  return 'from-cyan-600 to-cyan-400';
    case 'SCRAPING':  return 'from-orange-600 to-orange-400';
    case 'ANALYZING': return 'from-blue-600 to-blue-400';
    case 'WRITING':   return 'from-violet-600 to-violet-400';
    default:          return 'from-zinc-600 to-zinc-400';
  }
}

function statusStyle(status: Agent['status']) {
  switch (status) {
    case 'active':  return 'text-emerald-400 border-emerald-700/50 bg-emerald-900/20';
    case 'error':   return 'text-red-400 border-red-700/50 bg-red-900/20';
    case 'stopped': return 'text-zinc-500 border-zinc-700 bg-zinc-800/50';
    default:        return 'text-zinc-400 border-zinc-700 bg-zinc-800/50';
  }
}

export function AgentCard({ agent, onClick }: AgentCardProps): React.JSX.Element {
  return (
    <div
      onClick={onClick ? () => onClick(agent) : undefined}
      className={`rounded border border-zinc-800 bg-zinc-900/50 p-3.5 font-mono ${onClick ? 'cursor-pointer hover:border-zinc-700 transition-colors' : ''}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
            <svg className="h-2.5 w-2.5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <span className="text-[10px] font-bold tracking-widest text-zinc-200">{agent.name}</span>
        </div>
        <span className={`text-[9px] font-bold tracking-widest rounded px-1.5 py-0.5 uppercase border ${statusStyle(agent.status)}`}>
          {agent.status}
        </span>
      </div>
      <div className="text-[9px] text-zinc-600 tracking-wider mb-2">
        ID: {agent.id.slice(0, 8).toUpperCase()}
      </div>
      <div className="flex items-center justify-between mb-1">
        <span className={`text-[9px] tracking-widest font-bold ${activityColor(agent.activity)}`}>{agent.activity}</span>
        <span className={`text-[9px] font-bold ${activityColor(agent.activity)}`}>{agent.progress}%</span>
      </div>
      <div className="h-1 rounded-full bg-zinc-800 overflow-hidden mb-2.5">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${barColor(agent.activity)}`}
          style={{ width: `${agent.progress}%` }}
        />
      </div>
      <p className="text-[10px] text-zinc-500 italic leading-relaxed">
        &ldquo;{agent.description}&rdquo;
      </p>
    </div>
  );
}
