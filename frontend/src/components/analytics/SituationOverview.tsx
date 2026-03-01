import MetricCard from './MetricCard';
import type { Stats } from '@/data/types';

interface SituationOverviewProps {
  readonly stats: Stats;
}

export default function SituationOverview({ stats }: SituationOverviewProps) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white text-sm font-bold uppercase tracking-widest flex items-center gap-2">
          <span className="w-1 h-4 bg-primary" />
          Situation Overview
        </h3>
        <span className="text-xs font-mono text-slate-500">
          LAST UPDATED: {new Date().toLocaleTimeString('en-GB', { hour12: false })}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          label="Total Frames"
          value={stats.totalFrames.toLocaleString()}
          icon="videocam"
          trend={{ direction: 'up', text: '+12% vs avg' }}
        />
        <MetricCard
          label="Detections"
          value={stats.totalDetections.toLocaleString()}
          icon="center_focus_weak"
          trend={{ direction: 'down', text: '-2% drop' }}
        />
        <MetricCard
          label="Hazardous"
          value={stats.hazardousCount.toLocaleString()}
          icon="warning"
          trend={{ direction: 'up', text: '+45% spike' }}
        />
        <MetricCard
          label="Hazard Rate"
          value={`${stats.hazardRate}%`}
          icon="percent"
          trend={{ direction: 'up', text: '+0.5% critical' }}
        />
      </div>
    </section>
  );
}
