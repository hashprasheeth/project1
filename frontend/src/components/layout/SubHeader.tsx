import { useEffect, useState } from 'react';

export default function SubHeader() {
  const [time, setTime] = useState(formatUTC());

  useEffect(() => {
    const interval = setInterval(() => setTime(formatUTC()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-10 shrink-0 flex items-center justify-between px-4 md:px-6 bg-panel-dark border-b border-border-dark">
      <div className="flex items-center gap-2 text-primary/80 text-xs font-medium tracking-widest">
        <span className="material-symbols-outlined text-[14px]">terminal</span>
        <span className="hidden sm:inline">E-WASTE DETECTION SYSTEM // ACTIVE</span>
        <span className="sm:hidden">SYSTEM // ACTIVE</span>
      </div>
      <div className="text-text-dim text-xs font-mono tracking-wider">
        UTC {time}
      </div>
    </div>
  );
}

function formatUTC(): string {
  return new Date().toLocaleTimeString('en-GB', {
    hour12: false,
    timeZone: 'UTC',
  });
}
