'use client';

import { useState } from 'react';
import { CreateAgentRequest } from '@/types/agent';

interface CreateAgentFormProps {
  onSubmit: (data: CreateAgentRequest) => Promise<void>;
  loading?: boolean;
}

export function CreateAgentForm({ onSubmit, loading }: CreateAgentFormProps): React.JSX.Element {
  const [name, setName] = useState('');
  const [type, setType] = useState<CreateAgentRequest['type']>('research');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await onSubmit({ name, type, description });
      setName('');
      setDescription('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 font-mono">
      {error && <span className="text-[10px] text-red-400 tracking-wider">{error}</span>}
      <input
        type="text"
        placeholder="AGENT NAME"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-violet-500"
      />
      <select
        aria-label="Agent type"
        value={type}
        onChange={(e) => setType(e.target.value as CreateAgentRequest['type'])}
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-violet-500"
      >
        <option value="coding">CODING</option>
        <option value="research">RESEARCH</option>
        <option value="review">REVIEW</option>
        <option value="runtime">RUNTIME</option>
      </select>
      <textarea
        placeholder="DESCRIPTION"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={3}
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-violet-500 resize-none"
      />
      <button
        type="submit"
        disabled={loading || !name.trim()}
        className="bg-violet-700 hover:bg-violet-600 disabled:opacity-50 text-white text-[11px] font-bold tracking-widest py-2 rounded uppercase transition-colors"
      >
        {loading ? 'Spawning...' : 'Create Agent'}
      </button>
    </form>
  );
}
