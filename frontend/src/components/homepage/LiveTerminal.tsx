import type { LogEntry } from '@/data/types';
import { ScrollArea } from '@/components/ui/scroll-area';

interface LiveTerminalProps {
  readonly logs: readonly LogEntry[];
}

function logColor(level: LogEntry['level']): string {
  switch (level) {
    case 'danger': return 'text-danger';
    case 'warning': return 'text-warning';
    case 'info': return 'text-primary';
    case 'system': return 'text-text-dim';
  }
}

export default function LiveTerminal({ logs }: LiveTerminalProps) {
  return (
    <div className="h-64 border-b border-border-dark flex flex-col relative bg-panel-dark/50">
      <div className="p-4 border-b border-border-dark flex justify-between items-center bg-background-dark">
        <h3 className="section-label">
          <span className="material-symbols-outlined text-[14px]">terminal</span>
          LIVE LOGS
        </h3>
        <span className="text-[10px] text-primary animate-pulse">● REC</span>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 font-mono text-[10px] space-y-2 bg-black/30">
          {logs.slice(0, 20).map((log, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-text-dim shrink-0">{log.timestamp}</span>
              <span className={logColor(log.level)}>&gt; {log.message}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-text-dim">Awaiting system logs...</div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
