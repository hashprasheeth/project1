import { Progress } from '@/components/ui/progress';
import type { DispatchItem } from '@/data/types';

interface DispatchQueueProps {
  readonly items: readonly DispatchItem[];
}

function statusColor(status: DispatchItem['status']): string {
  switch (status) {
    case 'ready': return 'text-primary';
    case 'sorting': return 'text-warning';
    case 'queued': return 'text-slate-500';
    case 'dispatched': return 'text-accent-green';
  }
}

function iconBg(status: DispatchItem['status']): string {
  switch (status) {
    case 'ready': return 'bg-primary/20 text-primary border-primary/30';
    case 'sorting': return 'bg-warning/10 text-warning border-warning/30';
    default: return 'bg-slate-800 text-slate-400 border-slate-700';
  }
}

function indicatorColor(status: DispatchItem['status']): string {
  switch (status) {
    case 'ready': return 'bg-primary';
    case 'sorting': return 'bg-warning';
    default: return 'bg-slate-700';
  }
}

export default function DispatchQueue({ items }: DispatchQueueProps) {
  return (
    <div className="flex-1 flex flex-col p-4 overflow-hidden">
      <h3 className="section-label mb-3">
        <span className="material-symbols-outlined text-[14px]">local_shipping</span>
        DISPATCH QUEUE
      </h3>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {items.map((item) => (
          <div
            key={item.id}
            className={`bg-panel-dark border border-border-dark p-2 flex items-center gap-3 ${
              item.status === 'queued' ? 'opacity-60' : ''
            }`}
          >
            <div className={`w-8 h-8 flex items-center justify-center border ${iconBg(item.status)}`}>
              <span className="material-symbols-outlined text-[16px]">{item.icon}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center mb-1">
                <span className="text-white text-xs font-bold truncate">{item.batchName}</span>
                <span className={`text-[9px] uppercase ${statusColor(item.status)}`}>
                  {item.status === 'sorting' ? 'Sorting...' : item.status.toUpperCase()}
                </span>
              </div>
              <Progress value={item.progress} indicatorClassName={indicatorColor(item.status)} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
