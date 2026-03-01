import { useState, useMemo } from 'react';
import { EWASTE_CLASSES, RECYCLING_BINS, type EwasteClass, type RecyclingBin } from '@/data/ewaste-classes';

type HazardFilter = 'all' | 'hazardous' | 'safe';

export function useClassFilter() {
  const [searchText, setSearchText] = useState('');
  const [hazardFilter, setHazardFilter] = useState<HazardFilter>('all');
  const [activeBins, setActiveBins] = useState<Set<RecyclingBin>>(new Set(RECYCLING_BINS));

  const filteredClasses = useMemo<EwasteClass[]>(() => {
    return EWASTE_CLASSES.filter((cls) => {
      if (searchText && !cls.name.toLowerCase().includes(searchText.toLowerCase())) {
        return false;
      }
      if (hazardFilter === 'hazardous' && !cls.hazardous) return false;
      if (hazardFilter === 'safe' && cls.hazardous) return false;
      if (!activeBins.has(cls.recyclingBin)) return false;
      return true;
    });
  }, [searchText, hazardFilter, activeBins]);

  const toggleBin = (bin: RecyclingBin) => {
    setActiveBins((prev) => {
      const next = new Set(prev);
      if (next.has(bin)) next.delete(bin);
      else next.add(bin);
      return next;
    });
  };

  return {
    searchText,
    setSearchText,
    hazardFilter,
    setHazardFilter,
    activeBins,
    toggleBin,
    filteredClasses,
    totalCount: EWASTE_CLASSES.length,
  };
}
