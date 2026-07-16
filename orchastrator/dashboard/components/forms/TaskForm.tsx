'use client';

import { useState } from 'react';
import { CreateTaskRequest } from '@/types/task';

interface TaskFormProps {
  onSubmit: (data: CreateTaskRequest) => Promise<void>;
  loading?: boolean;
}

export function TaskForm({ onSubmit, loading }: TaskFormProps): React.JSX.Element {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<CreateTaskRequest['priority']>('medium');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await onSubmit({ title, description, priority });
      setTitle('');
      setDescription('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 font-mono">
      {error && <span className="text-[10px] text-red-400 tracking-wider">{error}</span>}
      <input
        type="text"
        placeholder="TASK TITLE"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-cyan-500"
      />
      <textarea
        placeholder="DESCRIPTION"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={3}
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-cyan-500 resize-none"
      />
      <select
        aria-label="Task priority"
        value={priority}
        onChange={(e) => setPriority(e.target.value as CreateTaskRequest['priority'])}
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-cyan-500"
      >
        <option value="low">LOW</option>
        <option value="medium">MEDIUM</option>
        <option value="high">HIGH</option>
      </select>
      <button
        type="submit"
        disabled={loading || !title.trim()}
        className="bg-cyan-700 hover:bg-cyan-600 disabled:opacity-50 text-white text-[11px] font-bold tracking-widest py-2 rounded uppercase transition-colors"
      >
        {loading ? 'Creating...' : 'Create Task'}
      </button>
    </form>
  );
}
