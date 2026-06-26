'use client';

import { useState } from 'react';

interface LoginFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  loading?: boolean;
}

export function LoginForm({ onSubmit, loading }: LoginFormProps): React.JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await onSubmit(email, password);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-72 font-mono">
      {error && <span className="text-[10px] text-red-400 tracking-wider">{error}</span>}
      <input
        type="email"
        placeholder="EMAIL"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-cyan-500"
      />
      <input
        type="password"
        placeholder="PASSWORD"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-cyan-500"
      />
      <button
        type="submit"
        disabled={loading}
        className="bg-cyan-700 hover:bg-cyan-600 disabled:opacity-50 text-white text-[11px] font-bold tracking-widest py-2 rounded uppercase transition-colors"
      >
        {loading ? 'Authenticating...' : 'Login'}
      </button>
    </form>
  );
}
