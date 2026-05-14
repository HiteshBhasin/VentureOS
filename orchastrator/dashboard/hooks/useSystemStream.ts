'use client';

import { useState, useEffect, useRef } from 'react';
import { StreamLog } from '@/types/task';

const MAX_LOGS = 50;

export function useSystemStream() {
  const [logs, setLogs] = useState<StreamLog[]>([]);
  const [connected, setConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const connect = () => {
      if (esRef.current) {
        esRef.current.close();
      }

      const es = new EventSource('/api/system/stream');
      esRef.current = es;

      es.onopen = () => setConnected(true);

      es.onmessage = (event) => {
        try {
          const log: StreamLog = JSON.parse(event.data);
          setLogs((prev) => {
            const next = [...prev, log];
            return next.length > MAX_LOGS ? next.slice(next.length - MAX_LOGS) : next;
          });
        } catch {
          // ignore malformed messages
        }
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        // Reconnect after 5s
        setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      esRef.current?.close();
    };
  }, []);

  return { logs, connected };
}
