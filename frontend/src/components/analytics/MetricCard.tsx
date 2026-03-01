interface MetricCardProps {
  readonly label: string;
  readonly value: string;
  readonly icon: string;
  readonly trend?: { direction: 'up' | 'down'; text: string };
}

export default function MetricCard({ label, value, icon, trend }: MetricCardProps) {
  return (
    <div className="bg-surface-dark border border-border-dark p-5 relative overflow-hidden group hover:border-primary/50 transition-colors">
      <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
        <span className="material-symbols-outlined text-4xl">{icon}</span>
      </div>
      <p className="metric-label mb-1">{label}</p>
      <p className="metric-value">{value}</p>
      {trend && (
        <div className={`flex items-center gap-1 text-xs mt-2 font-mono ${trend.direction === 'up' ? 'text-accent-green' : 'text-accent-red'}`}>
          <span className="material-symbols-outlined text-sm">
            {trend.direction === 'up' ? 'trending_up' : 'trending_down'}
          </span>
          <span>{trend.text}</span>
        </div>
      )}
    </div>
  );
}
