const FACILITIES = [
  { name: 'Hazardous Facility A', type: 'Battery / Chemical', status: 'Critical', statusColor: 'bg-accent-red text-background-dark', borderColor: 'border-accent-red' },
  { name: 'E-Waste Center 4', type: 'General Electronics', status: 'Active', statusColor: 'bg-primary text-background-dark', borderColor: 'border-primary' },
  { name: 'Metal Recovery Unit', type: 'Scrap / Copper', status: 'Active', statusColor: 'bg-primary text-background-dark', borderColor: 'border-primary' },
  { name: 'Plastic Sorting B', type: 'ABS / PVC', status: 'Pending', statusColor: 'bg-slate-700 text-white', borderColor: 'border-slate-500' },
  { name: 'Glass Recycling', type: 'Screens / Panels', status: 'Pending', statusColor: 'bg-slate-700 text-white', borderColor: 'border-slate-500' },
  { name: 'Refurbish Center', type: 'Laptops / Phones', status: 'Active', statusColor: 'bg-primary text-background-dark', borderColor: 'border-primary' },
] as const;

export default function RecyclingDispatch() {
  return (
    <section className="bg-surface-dark border border-border-dark p-5 flex-1">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-sm font-bold uppercase tracking-widest flex items-center gap-2">
          <span className="w-1 h-4 bg-slate-400" />
          Recycling Dispatch
        </h3>
        <span className="material-symbols-outlined text-slate-600">local_shipping</span>
      </div>
      <div className="flex flex-col gap-px bg-slate-800 border border-slate-800">
        <div className="grid grid-cols-[1fr_auto] bg-surface-dark p-2 text-[10px] font-mono text-slate-500 uppercase tracking-wider">
          <span>Facility / Type</span>
          <span>Status</span>
        </div>
        {FACILITIES.map((f) => (
          <div key={f.name} className={`grid grid-cols-[1fr_auto] items-center bg-[#151c19] p-2 hover:bg-white/5 transition-colors border-l-2 ${f.borderColor}`}>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-white uppercase">{f.name}</span>
              <span className="text-[10px] text-slate-400 font-mono">{f.type}</span>
            </div>
            <span className={`text-[10px] px-1.5 py-0.5 font-bold uppercase ${f.statusColor}`}>{f.status}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
