import { Progress } from '@/components/ui/progress';
import type { Stats } from '@/data/types';

interface HazardAssessmentProps {
  readonly hazardRate: number;
}

const THREAT_ITEMS = [
  { name: 'LITHIUM_LEAK', severity: 'Severe', color: 'border-accent-red', badgeBg: 'bg-accent-red/20 text-accent-red' },
  { name: 'BROKEN_CRT', severity: 'High', color: 'border-orange-500', badgeBg: 'bg-orange-500/20 text-orange-500' },
  { name: 'UNSORTED_CABLES', severity: 'Mod', color: 'border-yellow-500', badgeBg: 'bg-yellow-500/20 text-yellow-500' },
] as const;

export default function HazardAssessment({ hazardRate }: HazardAssessmentProps) {
  return (
    <section className="bg-surface-dark border border-border-dark p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-sm font-bold uppercase tracking-widest flex items-center gap-2">
          <span className="w-1 h-4 bg-accent-red" />
          Hazard Assessment
        </h3>
        <span className="material-symbols-outlined text-slate-600">report_problem</span>
      </div>

      <div className="flex items-end justify-between mb-2">
        <span className="metric-label">Criticality Index</span>
        <span className="text-accent-red text-4xl font-mono font-bold leading-none">{hazardRate}%</span>
      </div>

      <Progress value={hazardRate * 10} indicatorClassName="bg-accent-red" className="mb-6" />

      <div className="flex flex-col gap-2">
        {THREAT_ITEMS.map((t) => (
          <div key={t.name} className={`flex items-center justify-between p-2 bg-white/5 border-l-2 ${t.color}`}>
            <span className="text-xs font-mono text-white">{t.name}</span>
            <span className={`text-[10px] px-1 py-0.5 font-bold uppercase ${t.badgeBg}`}>{t.severity}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
