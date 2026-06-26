'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="flex flex-col h-full bg-[#080c18] text-zinc-300 font-mono p-5 gap-5 max-w-lg">
      <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">Settings</span>

      <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-[9px] tracking-widest text-zinc-600 uppercase">Account Email</span>
          <span className="text-[11px] text-zinc-300">{user?.email ?? 'Unknown'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[9px] tracking-widest text-zinc-600 uppercase">Role</span>
          <span className="text-[11px] text-zinc-300 uppercase">{user?.role ?? 'user'}</span>
        </div>
      </div>

      <button
        type="button"
        onClick={handleLogout}
        className="rounded border border-red-700/50 bg-red-900/20 text-red-400 text-[10px] font-bold tracking-widest px-4 py-2.5 uppercase hover:bg-red-900/40 transition-colors w-fit"
      >
        Log Out
      </button>
    </div>
  );
}
