'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { setToken, setUser } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? 'Login failed');
        return;
      }
      setToken(data.access_token);
      setUser({ id: data.user_id, email: data.email, name: '', role: 'user', createdAt: new Date().toISOString() });
      router.push('/');
    } catch {
      setError('Unable to reach server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-[#080c18] font-mono">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-72">
        <span className="text-[11px] tracking-widest text-zinc-400 uppercase mb-2">VentureOS Login</span>
        {error && <span className="text-[10px] text-red-400 tracking-wider">{error}</span>}
        <input
          type="email"
          placeholder="EMAIL"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-violet-500"
        />
        <input
          type="password"
          placeholder="PASSWORD"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-violet-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-violet-700 hover:bg-violet-600 disabled:opacity-50 text-white text-[11px] tracking-widest py-2 rounded uppercase"
        >
          {loading ? 'Authenticating...' : 'Login'}
        </button>
        <Link href="/signup" className="text-[10px] text-zinc-500 hover:text-zinc-300 tracking-widest text-center transition-colors">
          Don&apos;t have an account? Sign up
        </Link>
      </form>
    </div>
  );
}

