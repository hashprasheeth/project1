import type { Stats } from '@/data/types';

interface ClassDistributionProps {
  readonly classDistribution: Stats['classDistribution'];
}

export default function ClassDistribution({ classDistribution }: ClassDistributionProps) {
  return (
    <section className="flex-1 flex flex-col bg-surface-dark border border-border-dark p-5 h-full">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-white text-sm font-bold uppercase tracking-widest flex items-center gap-2 mb-1">
            Class Distribution
          </h3>
          <p className="text-xs text-slate-500 font-mono">TOP {classDistribution.length} DETECTED OBJECTS</p>
        </div>
        <span className="material-symbols-outlined text-slate-600">bar_chart</span>
      </div>
      <div className="flex flex-col gap-4 flex-1">
        {classDistribution.map((item) => (
          <div key={item.name} className="grid grid-cols-[100px_1fr_40px] items-center gap-3">
            <span className="text-slate-400 text-xs font-mono font-bold uppercase truncate text-right">
              {item.name.replace(/-/g, ' ').slice(0, 12)}
            </span>
            <div className="h-2 bg-slate-800 w-full relative">
              <div
                className={`absolute top-0 left-0 h-full ${item.percentage > 60 ? 'bg-primary' : 'bg-slate-600'}`}
                style={{ width: `${item.percentage}%` }}
              />
            </div>
            <span className="text-white text-xs font-mono text-right">{item.percentage}%</span>
          </div>
        ))}
      </div>
    </section>
  );
}
