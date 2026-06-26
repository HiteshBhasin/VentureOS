'use client';

import { useState, useEffect, useCallback } from 'react';
import { MemoryEntry } from '@/types/memory';
import { getMemoryEntries } from '@/lib/api';

export function useMemory() {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getMemoryEntries();
      setMemories(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch memory entries');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { memories, loading, error, refetch: refresh };
}
