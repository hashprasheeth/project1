import { useState, useEffect } from 'react';
import { fetchDispatchQueue } from '@/api/api';
import type { DispatchItem } from '@/data/types';

export function useDispatchQueue(pollIntervalMs = 5000) {
  const [items, setItems] = useState<DispatchItem[]>([]);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const data = await fetchDispatchQueue();
        if (active) setItems(data);
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

  return items;
}
