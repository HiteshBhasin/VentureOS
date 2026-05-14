'use client';

import { useState, useEffect, useCallback } from 'react';
import { SystemStatus } from '@/types/task';
import { getSystemStatus } from '@/lib/api';

const POLL_INTERVAL = 3000;

const DEFAULT: SystemStatus = {
  active_agents: 0,
  tokens_per_sec: 0,
  cost_estimate: 0,
  memory_used_gb: 0,
  memory_total_gb: 32,
  uptime_seconds: 0,
  latency_ms: 0,
};

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus>(DEFAULT);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getSystemStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [refresh]);

  return { status, loading, error, refetch: refresh };
}
