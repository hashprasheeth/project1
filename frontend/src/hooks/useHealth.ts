import { useState, useEffect } from 'react';
import { fetchHealth } from '@/api/api';
import type { HealthStatus } from '@/data/types';

const DEFAULT_HEALTH: HealthStatus = {
  systemOnline: false,
  tritonStatus: 'offline',
  modelStatus: 'offline',
  gpuLoad: 0,
  memoryUsage: 0,
  latencyMs: 0,
  framesProcessed: 0,
};

export function useHealth(pollIntervalMs = 5000) {
  const [health, setHealth] = useState<HealthStatus>(DEFAULT_HEALTH);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const data = await fetchHealth();
        if (active) setHealth(data);
      } catch {
        if (active) setHealth((h) => ({ ...h, systemOnline: false }));
      }
    };

    poll();
    const id = setInterval(poll, pollIntervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [pollIntervalMs]);

  return health;
}
