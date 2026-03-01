import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { Detection } from '@/data/types';

interface LiveLogTableProps {
  readonly detections: readonly Detection[];
}

export default function LiveLogTable({ detections }: LiveLogTableProps) {
  const recent = detections.slice(0, 15);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="panel-header">
        <span className="text-[10px] text-text-dim font-bold tracking-widest">LIVE LOG</span>
        <span className="text-[10px] text-primary cursor-pointer hover:underline">VIEW ALL</span>
      </div>
      <div className="flex-1 overflow-y-auto bg-background-dark">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Class</TableHead>
              <TableHead>Conf</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recent.map((d) => (
              <TableRow key={d.id + d.timestamp}>
                <TableCell className="text-text-dim">{d.id}</TableCell>
                <TableCell className="text-white">{d.timestamp}</TableCell>
                <TableCell className={d.hazardous ? 'text-danger font-bold' : d.confidence < 0.6 ? 'text-warning font-bold' : 'text-primary font-bold'}>
                  {d.className.replace(/-/g, ' ').slice(0, 12)}
                </TableCell>
                <TableCell className="text-text-dim">{Math.round(d.confidence * 100)}%</TableCell>
                <TableCell>
                  {d.hazardous ? (
                    <Badge variant="danger">FLAGGED</Badge>
                  ) : d.confidence < 0.6 ? (
                    <Badge variant="warning">REVIEW</Badge>
                  ) : (
                    <Badge variant="default">CLEARED</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {recent.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-text-dim py-8">
                  Awaiting detections...
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
