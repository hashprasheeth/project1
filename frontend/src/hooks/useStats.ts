import { useState, useEffect, useCallback } from 'react';
import { fetchStats, resetTracking } from '@/api/api';
import type { Stats } from '@/data/types';

const DEFAULT_STATS: Stats = {
  totalFrames: 0,
  totalDetections: 0,
  hazardousCount: 0,
  hazardRate: 0,
  classDistribution: [],
  recentTrend: [],
};

export function useStats(pollIntervalMs = 3000) {
  const [stats, setStats] = useState<Stats>(DEFAULT_STATS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const data = await fetchStats();
        if (active) {
          setStats(data);
          setLoading(false);
        }
      } catch {
        // silently retry
      }
    };

    poll();
    const id = setInterval(poll, pollIntervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [pollIntervalMs]);

  const reset = useCallback(async () => {
    await resetTracking();
    setStats(DEFAULT_STATS);
  }, []);

  return { stats, loading, reset };
}
