import { Progress } from '@/components/ui/progress';
import { useStats } from '@/hooks/useStats';

export default function ThroughputStats() {
  const { stats } = useStats(3000);

  const itemsProcessed = stats.totalDetections;
  const recycledMassKg = Math.round(stats.totalDetections * 0.67);
  const processedPct = Math.min(100, Math.round((stats.totalFrames / 1000) * 100));
  const recycledPct = Math.min(100, Math.round((recycledMassKg / 1500) * 100));

  return (
    <div className="p-4 flex-1">
      <h3 className="section-label mb-4">
        <span className="material-symbols-outlined text-[14px]">analytics</span>
        THROUGHPUT
      </h3>

      <div className="grid grid-cols-1 gap-3">
        <div className="bg-panel-dark border border-border-dark p-3 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-1 opacity-20">
            <span className="material-symbols-outlined">conveyor_belt</span>
          </div>
          <p className="text-[10px] text-text-dim uppercase">Items Processed</p>
          <p className="text-2xl font-bold text-white mt-1">{itemsProcessed.toLocaleString()}</p>
          <Progress value={processedPct} className="mt-2" />
        </div>

        <div className="bg-panel-dark border border-border-dark p-3 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-1 opacity-20">
            <span className="material-symbols-outlined">recycling</span>
          </div>
          <p className="text-[10px] text-text-dim uppercase">Recycled Mass</p>
          <p className="text-2xl font-bold text-white mt-1">
            {recycledMassKg.toLocaleString()} <span className="text-sm text-text-dim">KG</span>
          </p>
          <Progress value={recycledPct} indicatorClassName="bg-blue-500" className="mt-2" />
        </div>
      </div>

      <div className="mt-6 border-t border-border-dark pt-4">
        <p className="text-[10px] text-text-dim uppercase mb-2">System Load</p>
        <div className="flex gap-1 h-8 items-end">
          {[40, 60, 30, 80, 90, 50, 45, 70].map((h, i) => (
            <div key={i} className="flex-1 bg-primary/20" style={{ height: `${h}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}
