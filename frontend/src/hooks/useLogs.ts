import { useState, useEffect } from 'react';
import { fetchLogs } from '@/api/api';
import type { LogEntry } from '@/data/types';

export function useLogs(pollIntervalMs = 3000) {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const newLogs = await fetchLogs();
        if (active) {
          setLogs((prev) => [...newLogs, ...prev].slice(0, 100));
        }
      } catch {
        // silent
      }
    };

    poll();
    const id = setInterval(poll, pollIntervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [pollIntervalMs]);

  return logs;
}
