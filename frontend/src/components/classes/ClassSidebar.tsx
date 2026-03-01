import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { RECYCLING_BINS, type RecyclingBin } from '@/data/ewaste-classes';

interface ClassSidebarProps {
  readonly totalCount: number;
  readonly filteredCount: number;
  readonly searchText: string;
  readonly onSearchChange: (val: string) => void;
  readonly hazardFilter: 'all' | 'hazardous' | 'safe';
  readonly onHazardFilterChange: (val: 'all' | 'hazardous' | 'safe') => void;
  readonly activeBins: Set<RecyclingBin>;
  readonly onToggleBin: (bin: RecyclingBin) => void;
}

const BIN_COUNTS: Record<string, number> = {
  'E-Waste': 18,
  'Battery': 7,
  'Hazardous Facility': 18,
  'Metal Recovery': 0,
  'Appliance': 14,
  'Data Destruction': 6,
  'Medical Waste': 4,
  'General Recycling': 2,
  'Glass': 0,
  'Plastic Sorting': 0,
};

export default function ClassSidebar({
  totalCount,
  filteredCount,
  searchText,
  onSearchChange,
  hazardFilter,
  onHazardFilterChange,
  activeBins,
  onToggleBin,
}: ClassSidebarProps) {
  return (
    <div className="flex flex-col gap-8 p-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <p className="text-slate-400 text-xs font-mono uppercase tracking-widest">Database Status</p>
        <div className="flex items-baseline gap-2">
          <h1 className="text-3xl font-black text-white tracking-tighter">{totalCount}</h1>
          <span className="text-primary font-bold uppercase tracking-widest text-sm">Objects Indexed</span>
        </div>
        {filteredCount !== totalCount && (
          <p className="text-text-dim text-xs font-mono">{filteredCount} matching filters</p>
        )}
      </div>

      {/* Search */}
      <div className="relative w-full">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-400">
          <span className="material-symbols-outlined text-lg">search</span>
        </div>
        <Input
          className="pl-10"
          placeholder="SEARCH ID OR CLASS..."
          value={searchText}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      {/* Quick Filters */}
      <div className="space-y-3">
        <p className="text-slate-400 text-xs font-mono uppercase tracking-widest mb-2">Classification</p>
        <div className="flex gap-2">
          {(['all', 'hazardous', 'safe'] as const).map((f) => (
            <button
              key={f}
              onClick={() => onHazardFilterChange(f)}
              className={`flex-1 py-2 font-bold text-xs uppercase tracking-wider transition-all ${
                hazardFilter === f
                  ? f === 'hazardous'
                    ? 'bg-danger text-black'
                    : f === 'safe'
                    ? 'bg-primary text-black'
                    : 'bg-primary text-background-dark'
                  : f === 'hazardous'
                  ? 'bg-transparent border border-danger text-danger hover:bg-danger/10'
                  : f === 'safe'
                  ? 'bg-transparent border border-primary text-primary hover:bg-primary/10'
                  : 'bg-transparent border border-border-dark text-text-dim hover:bg-panel-dark'
              }`}
            >
              {f === 'all' ? 'All' : f === 'hazardous' ? 'Hazard' : 'Safe'}
            </button>
          ))}
        </div>
      </div>

      {/* Recycling Streams */}
      <div className="space-y-1">
        <p className="text-slate-400 text-xs font-mono uppercase tracking-widest mb-3">Recycling Streams</p>
        {RECYCLING_BINS.filter((b) => (BIN_COUNTS[b] ?? 0) > 0).map((bin) => (
          <label
            key={bin}
            className="flex items-center justify-between group cursor-pointer hover:bg-surface-dark p-2 -mx-2 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Checkbox
                checked={activeBins.has(bin)}
                onCheckedChange={() => onToggleBin(bin)}
              />
              <span className="text-sm font-mono text-slate-300 group-hover:text-primary transition-colors uppercase">
                {bin}
              </span>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-panel-dark px-1.5 py-0.5">
              {BIN_COUNTS[bin] ?? 0}
            </span>
          </label>
        ))}
      </div>

      {/* System Info */}
      <div className="mt-auto pt-6 border-t border-border-dark">
        <div className="flex flex-col gap-2 text-[10px] font-mono text-slate-500 uppercase">
          <div className="flex justify-between">
            <span>System Ver:</span>
            <span className="text-slate-300">2.4.0-RC</span>
          </div>
          <div className="flex justify-between">
            <span>Node Status:</span>
            <span className="text-primary animate-pulse">ONLINE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
