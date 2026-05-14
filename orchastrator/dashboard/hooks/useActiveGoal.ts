'use client';

import { useState, useEffect, useCallback } from 'react';
import { ActiveGoal } from '@/types/task';
import { getActiveGoal } from '@/lib/api';

const POLL_INTERVAL = 5000;

const DEFAULT: ActiveGoal = {
  id: '',
  title: '',
  status: 'executing',
  completion: 0,
  elapsed_seconds: 0,
  pid: 0,
  memory_used_gb: 0,
  memory_total_gb: 32,
};

export function useActiveGoal() {
  const [goal, setGoal] = useState<ActiveGoal>(DEFAULT);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getActiveGoal();
      setGoal(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch active goal');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [refresh]);

  return { goal, loading, error, refetch: refresh };
}
