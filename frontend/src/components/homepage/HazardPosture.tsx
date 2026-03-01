import { Button } from '@/components/ui/button';

interface HazardPostureProps {
  readonly hasHazard: boolean;
}

export default function HazardPosture({ hasHazard }: HazardPostureProps) {
  return (
    <div className="p-4 border-b border-border-dark bg-danger/5">
      <h3 className="text-danger text-xs font-bold tracking-widest mb-3 flex items-center gap-2">
        <span className="material-symbols-outlined text-[14px]">security</span>
        HAZARD POSTURE
      </h3>

      <div className="border border-danger/30 p-4 bg-black/40 relative overflow-hidden">
        <div className="flex justify-between items-end mb-2">
          <span className="text-4xl font-bold text-danger leading-none">
            {hasHazard ? 'CRIT' : 'NORM'}
          </span>
          <span className="text-xs text-danger/80 mb-1">
            LVL {hasHazard ? '3' : '0'}
          </span>
        </div>
        <p className="text-[10px] text-danger/70 leading-relaxed uppercase">
          {hasHazard
            ? 'Containment protocols active. Manual override required for belt restart.'
            : 'All systems nominal. No hazardous items in current scan window.'}
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-1 hazard-stripes" />
      </div>

      <Button variant="destructive" className="w-full mt-3" size="sm">
        {hasHazard ? 'Initiate Lockdown' : 'System Normal'}
      </Button>
    </div>
  );
}
