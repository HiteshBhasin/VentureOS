'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  // Start at null on both server AND the client's hydration pass — reading
  // `typeof window` in the initializer made the client's first render diverge
  // from the server's immediately, which is a hydration mismatch. The actual
  // check only happens after mount, in an effect (client-only, post-hydration).
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    setAuthenticated(isAuthenticated());
  }, []);

  useEffect(() => {
    if (authenticated === false) {
      router.replace('/login');
    }
  }, [authenticated, router]);

  if (authenticated === null) return null; // still checking — matches server render
  if (!authenticated) return null;
  return <>{children}</>;
}
