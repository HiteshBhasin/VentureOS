'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Task } from '@/types/task';
import { getTask } from '@/lib/api';
import { Loading } from '@/components/common/Loading';
import { Error as ErrorView } from '@/components/common/Error';

function statusStyle(status: Task['status']) {
  switch (status) {
    case 'completed': return 'text-emerald-400 border-emerald-700/50 bg-emerald-900/20';
    case 'running':   return 'text-cyan-400 border-cyan-600/50 bg-cyan-900/20';
    case 'failed':    return 'text-red-400 border-red-700/50 bg-red-900/20';
    default:          return 'text-zinc-500 border-zinc-700 bg-zinc-800/50';
  }
}

export default function DetailPage() {
  const params = useParams<{ id: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTask(params.id);
      setTask(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Task not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  if (loading) return <Loading />;
  if (error || !task) return <ErrorView message={error ?? 'Task not found'} onRetry={load} />;

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-4">
      <Link href="/tasks" className="text-[9px] tracking-widest text-zinc-600 hover:text-zinc-400 uppercase w-fit transition-colors">
        &larr; Back to Tasks
      </Link>

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white tracking-tight">{task.title}</h1>
        <span className={`text-[9px] font-bold tracking-widest border rounded px-1.5 py-0.5 uppercase ${statusStyle(task.status)}`}>
          {task.status}
        </span>
      </div>

      <p className="text-[11px] text-zinc-500 leading-relaxed">{task.description || 'No description provided.'}</p>

      <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden max-w-sm">
        <div className="h-full rounded-full bg-gradient-to-r from-cyan-700 to-cyan-400" style={{ width: `${task.progress}%` }} />
      </div>

      <div className="grid grid-cols-2 gap-3 max-w-md rounded border border-zinc-800 bg-zinc-900/50 p-4 text-[10px] text-zinc-500">
        <span>ID: <span className="text-zinc-300">{task.id}</span></span>
        <span>Priority: <span className="text-zinc-300 uppercase">{task.priority}</span></span>
        <span>Agent: <span className="text-zinc-300">{task.agent_id ?? 'Unassigned'}</span></span>
        <span>Progress: <span className="text-zinc-300">{task.progress}%</span></span>
        <span>Created: <span className="text-zinc-300">{task.created_at ? new Date(task.created_at).toLocaleString() : '—'}</span></span>
        <span>Updated: <span className="text-zinc-300">{task.updated_at ? new Date(task.updated_at).toLocaleString() : '—'}</span></span>
      </div>

      {task.tags.length > 0 && (
        <div className="flex items-center gap-2">
          {task.tags.map((tag) => (
            <span key={tag} className="text-[9px] text-zinc-600 border border-zinc-700 rounded px-1.5 py-0.5 tracking-wider uppercase">{tag}</span>
          ))}
        </div>
      )}

      {task.result?.project_path && (
        <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4 max-w-md">
          <div className="text-[9px] text-zinc-600 tracking-widest uppercase mb-1.5">Project Output</div>
          <code className="text-[10px] text-cyan-400 break-all">{task.result.project_path}</code>
        </div>
      )}
    </div>
  );
}
