import { Checkbox } from '@/components/ui/checkbox';

const TIME_FILTERS = ['1H', '6H', '24H', '48H', '7D', 'ALL'] as const;

const CATEGORIES = [
  { label: 'HAZARDOUS', color: 'bg-danger', hoverBorder: 'hover:border-danger/50', checkColor: 'data-[state=checked]:bg-danger data-[state=checked]:border-danger', defaultChecked: true },
  { label: 'APPLIANCES', color: 'bg-primary', hoverBorder: 'hover:border-primary/50', checkColor: 'data-[state=checked]:bg-primary data-[state=checked]:border-primary', defaultChecked: true },
  { label: 'ELECTRONICS', color: 'bg-warning', hoverBorder: 'hover:border-warning/50', checkColor: 'data-[state=checked]:bg-warning data-[state=checked]:border-warning', defaultChecked: true },
  { label: 'MEDICAL', color: 'bg-purple-500', hoverBorder: 'hover:border-purple-500/50', checkColor: 'data-[state=checked]:bg-purple-500 data-[state=checked]:border-purple-500', defaultChecked: false },
] as const;

export default function DetectionScope() {
  return (
    <div className="p-4 border-b border-border-dark">
      <h3 className="section-label mb-4">
        <span className="material-symbols-outlined text-[14px]">filter_list</span>
        DETECTION SCOPE
      </h3>

      <div className="grid grid-cols-3 gap-2 mb-6">
        {TIME_FILTERS.map((t, i) => (
          <button
            key={t}
            className={`text-xs py-1 border transition-all ${
              i === 0
                ? 'bg-primary/20 text-primary border-primary/40 hover:bg-primary hover:text-black'
                : 'bg-panel-dark text-text-dim border-border-dark hover:border-primary/50 hover:text-white'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {CATEGORIES.map((cat) => (
          <label
            key={cat.label}
            className={`flex items-center justify-between group cursor-pointer p-2 bg-panel-dark border border-border-dark ${cat.hoverBorder}`}
          >
            <div className="flex items-center gap-3">
              <span className={`w-2 h-2 rounded-full ${cat.color} ${cat.label === 'HAZARDOUS' ? 'animate-pulse' : ''}`} />
              <span className="text-xs font-bold text-slate-200">{cat.label}</span>
            </div>
            <Checkbox defaultChecked={cat.defaultChecked} className={cat.checkColor} />
          </label>
        ))}
      </div>
    </div>
  );
}
