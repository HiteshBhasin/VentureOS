'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  // Lazy initializer: null on server (SSR safe), actual token check on client
  const [authenticated] = useState<boolean | null>(() => {
    if (typeof window === 'undefined') return null;
    return isAuthenticated();
  });

  useEffect(() => {
    if (authenticated === false) {
      router.replace('/login');
    }
  }, [authenticated, router]);

  if (authenticated === null) return null; // still checking — matches server render
  if (!authenticated) return null;
  return <>{children}</>;
}
