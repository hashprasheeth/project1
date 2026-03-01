import type { EwasteClass } from '@/data/ewaste-classes';
import ClassCard from './ClassCard';

interface ClassGridProps {
  readonly classes: readonly EwasteClass[];
}

export default function ClassGrid({ classes }: ClassGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {classes.map((cls) => (
        <ClassCard key={cls.id} cls={cls} />
      ))}
      {classes.length === 0 && (
        <div className="col-span-full flex flex-col items-center justify-center py-20 text-text-dim">
          <span className="material-symbols-outlined text-5xl mb-4">search_off</span>
          <p className="text-lg font-bold">No classes match your filters</p>
          <p className="text-sm mt-1">Try adjusting your search or filter criteria</p>
        </div>
      )}
    </div>
  );
}
