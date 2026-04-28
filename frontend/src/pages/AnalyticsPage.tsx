import { useStats } from '@/hooks/useStats';
import { useHealth } from '@/hooks/useHealth';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import SituationOverview from '@/components/analytics/SituationOverview';
import ClassDistribution from '@/components/analytics/ClassDistribution';
import ThreatTimeline from '@/components/analytics/ThreatTimeline';
import HazardAssessment from '@/components/analytics/HazardAssessment';
import RecyclingDispatch from '@/components/analytics/RecyclingDispatch';
import SystemTelemetry from '@/components/analytics/SystemTelemetry';

export default function AnalyticsPage() {
  const { stats, reset } = useStats(3000);
  const health = useHealth(5000);

  return (
    <ScrollArea className="h-full">
      <div className="w-full max-w-[1440px] mx-auto p-4 md:p-6 lg:p-8 flex flex-col gap-6">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-end gap-4 border-b border-border-dark pb-6">
          <div className="flex min-w-72 flex-col gap-2">
            <div className="flex items-center gap-2 text-primary/60 text-xs font-mono uppercase tracking-widest">
              <span className="material-symbols-outlined text-[16px]">radar</span>
              <span>System Status: {health.systemOnline ? 'Online' : 'Offline'}</span>
              <span>|</span>
              <span>Latency: {health.latencyMs}ms</span>
            </div>
            <h1 className="text-white tracking-tight text-3xl md:text-4xl font-bold uppercase font-display">
              Detection Analytics
            </h1>
            <p className="text-slate-400 text-sm font-mono uppercase tracking-wider">
              Real-time e-waste hazard monitoring &amp; classification
            </p>
          </div>
          <Button variant="outline" onClick={reset} className="group">
            <span className="material-symbols-outlined group-hover:rotate-180 transition-transform mr-2">refresh</span>
            Reset Stats
          </Button>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          {/* Left column */}
          <div className="xl:col-span-8 flex flex-col gap-6">
            <SituationOverview stats={stats} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ClassDistribution classDistribution={stats.classDistribution} />
              <ThreatTimeline data={stats.recentTrend} />
            </div>
          </div>

          {/* Right column */}
          <div className="xl:col-span-4 flex flex-col gap-6">
            <HazardAssessment hazardRate={stats.hazardRate} />
            <RecyclingDispatch />
            <SystemTelemetry health={health} />
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
