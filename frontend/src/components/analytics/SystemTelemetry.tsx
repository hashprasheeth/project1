import type { HealthStatus } from '@/data/types';

interface SystemTelemetryProps {
  readonly health: HealthStatus;
}

function SegmentedBar({ label, value }: { label: string; value: number }) {
  const segments = 6;
  const filled = Math.round((value / 100) * segments);
  return (
    <div>
      <div className="flex justify-between text-[10px] font-mono uppercase text-slate-400 mb-1">
        <span>{label}</span>
        <span className="text-primary">{value}%</span>
      </div>
      <div className="h-1.5 bg-slate-800 w-full flex gap-0.5">
        {Array.from({ length: segments }, (_, i) => (
          <div key={i} className={`h-full flex-1 ${i < filled ? 'bg-primary' : 'bg-slate-700'}`} />
        ))}
      </div>
    </div>
  );
}

function StatusDot({ label, active }: { label: string; active: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${active ? 'bg-accent-green shadow-[0_0_8px_#0bda49]' : 'bg-slate-600'}`} />
      <span className="text-[10px] font-mono text-slate-300 uppercase">{label}</span>
    </div>
  );
}

export default function SystemTelemetry({ health }: SystemTelemetryProps) {
  return (
    <section className="bg-surface-dark border border-border-dark p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-sm font-bold uppercase tracking-widest flex items-center gap-2">
          <span className="w-1 h-4 bg-slate-600" />
          System Telemetry
        </h3>
        <span className="material-symbols-outlined text-slate-600">memory</span>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <SegmentedBar label="GPU Load" value={health.gpuLoad} />
        <SegmentedBar label="Memory" value={health.memoryUsage} />
      </div>
      <div className="flex items-center justify-between border-t border-slate-800 pt-3">
        <StatusDot label="Triton Inference" active={health.tritonStatus === 'active'} />
        <StatusDot label="YOLOv8 Model" active={health.modelStatus === 'active'} />
      </div>
    </section>
  );
}
