import Link from 'next/link';
import { Task } from '@/types/task';
import { Loading } from '@/components/common/Loading';

interface TaskListProps {
  tasks: Task[];
  loading?: boolean;
}

function statusBadge(status: Task['status']) {
  switch (status) {
    case 'completed': return { label: 'Success',    cls: 'text-emerald-400 border-emerald-700/50 bg-emerald-900/20' };
    case 'running':   return { label: 'Processing', cls: 'text-cyan-400 border-cyan-600/50 bg-cyan-900/20' };
    case 'failed':    return { label: 'Failed',     cls: 'text-red-400 border-red-700/50 bg-red-900/20' };
    default:          return { label: 'Queue',      cls: 'text-zinc-600 border-zinc-700 bg-zinc-800/50' };
  }
}

function TaskRow({ task }: { task: Task }) {
  const { label, cls } = statusBadge(task.status);
  const isRunning   = task.status === 'running';
  const isCompleted = task.status === 'completed';
  const isQueue     = task.status === 'queued' || task.status === 'pending';

  return (
    <Link
      href={`/${task.id}`}
      className={`block rounded border p-4 transition-colors hover:border-zinc-700 ${
        isRunning   ? 'border-cyan-500/30 bg-zinc-900/50' :
        isQueue     ? 'border-zinc-800 bg-zinc-900/30 opacity-60' :
                      'border-zinc-800 bg-zinc-900/50'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 h-6 w-6 shrink-0 rounded-full flex items-center justify-center ${
          isCompleted ? 'bg-emerald-500/15 border border-emerald-500/40' :
          isRunning   ? 'bg-cyan-500/15 border border-cyan-500/40' :
                        'bg-zinc-800 border border-zinc-700'
        }`}>
          {isCompleted && (
            <svg className="h-3 w-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          )}
          {isRunning && (
            <svg className="h-3 w-3 text-cyan-400 animate-spin [animation-duration:1.5s]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          )}
          {isQueue && (
            <svg className="h-3 w-3 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1.5">
            <span className={`text-sm font-bold ${isQueue ? 'text-zinc-400' : 'text-white'}`}>{task.title}</span>
            <span className={`text-[9px] font-bold tracking-widest border rounded px-1.5 py-0.5 uppercase flex items-center gap-1 ${cls}`}>
              {isRunning && <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />}
              {label}
            </span>
          </div>
          <p className={`text-[11px] leading-relaxed ${isQueue ? 'text-zinc-600' : 'text-zinc-500'}`}>{task.description}</p>

          {isRunning && (
            <div className="mt-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[9px] text-zinc-600 tracking-wider uppercase truncate max-w-[160px]">
                  {task.tags[0] ?? 'Processing...'}
                </span>
                <span className="text-[9px] text-cyan-500 font-bold">{task.progress}%</span>
              </div>
              <div className="h-1 rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-700 to-cyan-400"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>
          )}

          {isCompleted && task.tags.length > 0 && (
            <div className="flex items-center gap-2 mt-2.5">
              {task.tags.map((tag) => (
                <span key={tag} className="text-[9px] text-zinc-600 border border-zinc-700 rounded px-1.5 py-0.5 tracking-wider uppercase">{tag}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

export function TaskList({ tasks, loading }: TaskListProps): React.JSX.Element {
  if (loading) return <Loading />;

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 font-mono">
        <span className="text-[11px] tracking-widest text-zinc-600 uppercase">No tasks yet</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 font-mono">
      {tasks.map((task) => (
        <TaskRow key={task.id} task={task} />
      ))}
    </div>
  );
}
