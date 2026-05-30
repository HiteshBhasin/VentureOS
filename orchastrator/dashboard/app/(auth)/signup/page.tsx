'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? 'Signup failed');
        return;
      }
      setSuccess(data.message ?? 'Account created. Check your email to confirm, then log in.');
    } catch {
      setError('Unable to reach server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-[#080c18] font-mono">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-72">
        <span className="text-[11px] tracking-widest text-zinc-400 uppercase mb-2">VentureOS Sign Up</span>
        {error && <span className="text-[10px] text-red-400 tracking-wider">{error}</span>}
        {success && (
          <div className="flex flex-col gap-2">
            <span className="text-[10px] text-emerald-400 tracking-wider">{success}</span>
            <Link href="/login" className="text-[10px] text-violet-400 hover:text-violet-300 tracking-widest transition-colors">
              → Go to Login
            </Link>
          </div>
        )}
        {!success && (
          <>
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
            <input
              type="password"
              placeholder="CONFIRM PASSWORD"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
              className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-[11px] tracking-widest px-3 py-2 rounded outline-none focus:border-violet-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-violet-700 hover:bg-violet-600 disabled:opacity-50 text-white text-[11px] tracking-widest py-2 rounded uppercase"
            >
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
            <Link href="/login" className="text-[10px] text-zinc-500 hover:text-zinc-300 tracking-widest text-center transition-colors">
              Already have an account? Log in
            </Link>
          </>
        )}
      </form>
    </div>
  );
}


