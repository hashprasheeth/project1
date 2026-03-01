interface ThreatTimelineProps {
  readonly data: readonly number[];
}

export default function ThreatTimeline({ data }: ThreatTimelineProps) {
  const max = Math.max(...data, 1);
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 300;
    const y = 100 - (v / max) * 90;
    return `${x},${y}`;
  });

  const linePath = `M${points.join(' L')}`;
  const areaPath = `${linePath} L300,100 L0,100 Z`;

  return (
    <section className="flex-1 flex flex-col bg-surface-dark border border-border-dark p-5 h-full">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white text-sm font-bold uppercase tracking-widest flex items-center gap-2 mb-1">
            Threat Timeline
          </h3>
          <p className="text-xs text-slate-500 font-mono">HAZARD SPIKES (24H)</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-accent-red">
          <span className="w-2 h-2 rounded-full bg-accent-red animate-pulse" />
          LIVE
        </div>
      </div>
      <div className="flex-1 flex flex-col justify-end min-h-[200px] relative">
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="w-full h-px bg-slate-500" />
          ))}
        </div>
        <svg className="w-full h-full z-10" viewBox="0 0 300 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fa5838" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#fa5838" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={areaPath} fill="url(#chartGradient)" />
          <path d={linePath} fill="none" stroke="#fa5838" strokeWidth="2" />
        </svg>
        <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-2 pt-2 border-t border-slate-800">
          <span>00:00</span>
          <span>06:00</span>
          <span>12:00</span>
          <span>18:00</span>
          <span>24:00</span>
        </div>
      </div>
    </section>
  );
}
