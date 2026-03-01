import { Badge } from '@/components/ui/badge';
import type { EwasteClass } from '@/data/ewaste-classes';

interface ClassCardProps {
  readonly cls: EwasteClass;
}

export default function ClassCard({ cls }: ClassCardProps) {
  const borderColor = cls.hazardous ? 'border-l-danger' : 'border-l-primary';
  const hoverBorder = cls.hazardous ? 'group-hover:border-danger/40' : 'group-hover:border-primary/40';

  return (
    <div className={`group relative flex flex-col bg-surface-dark border-l-2 ${borderColor} border border-border-dark hover:shadow-md hover:translate-y-[-2px] transition-all overflow-hidden h-full`}>
      <div className="absolute top-0 right-0 p-2 opacity-50 group-hover:opacity-100 transition-opacity">
        <span className="material-symbols-outlined text-slate-600 text-lg">more_horiz</span>
      </div>

      <div className="p-5 flex flex-col h-full">
        <div className="flex justify-between items-start mb-3">
          <Badge variant={cls.hazardous ? 'danger' : 'default'}>
            {cls.hazardous ? 'Hazardous' : 'Safe'}
          </Badge>
          <span className="text-slate-500 font-mono text-[10px]">ID: {String(cls.id).padStart(3, '0')}</span>
        </div>

        <div className={`h-24 w-full bg-background-dark mb-4 flex items-center justify-center border border-dashed border-border-dark ${hoverBorder} transition-colors`}>
          <span className="material-symbols-outlined text-4xl text-slate-700">
            {cls.hazardous ? 'warning' : 'recycling'}
          </span>
        </div>

        <h3 className="text-lg font-bold text-white font-mono uppercase mb-1 truncate">
          {cls.name.replace(/-/g, '_')}
        </h3>
        <p className="text-xs text-slate-500 uppercase tracking-wide mb-4">
          Stream: {cls.recyclingBin}
        </p>

        <p className="text-[11px] text-text-dim leading-relaxed mb-4 line-clamp-2">
          {cls.description}
        </p>

        <div className="mt-auto grid grid-cols-2 gap-2 border-t border-border-dark pt-3">
          <div>
            <p className="text-[10px] text-slate-400 font-mono uppercase">Confidence</p>
            <p className="text-sm font-bold text-primary font-mono">
              {(85 + Math.random() * 15).toFixed(1)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-slate-400 font-mono uppercase">Frequency</p>
            <p className="text-sm font-bold text-white font-mono">
              {['Low', 'Med', 'High', 'V.High'][Math.floor(Math.random() * 4)]}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
