import { useClassFilter } from '@/hooks/useClassFilter';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import ClassSidebar from '@/components/classes/ClassSidebar';
import ClassGrid from '@/components/classes/ClassGrid';

export default function ClassExplorerPage() {
  const {
    searchText,
    setSearchText,
    hazardFilter,
    setHazardFilter,
    activeBins,
    toggleBin,
    filteredClasses,
    totalCount,
  } = useClassFilter();

  const sidebarProps = {
    totalCount,
    filteredCount: filteredClasses.length,
    searchText,
    onSearchChange: setSearchText,
    hazardFilter,
    onHazardFilterChange: setHazardFilter,
    activeBins,
    onToggleBin: toggleBin,
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-80 shrink-0 border-r border-border-dark bg-[#0c1a15] flex-col overflow-y-auto">
        <ClassSidebar {...sidebarProps} />
      </aside>

      {/* Main content */}
      <ScrollArea className="flex-1">
        <section className="p-6 md:p-10">
          {/* Mobile filter trigger */}
          <div className="lg:hidden mb-6">
            <Sheet>
              <SheetTrigger asChild>
                <button className="flex items-center gap-2 text-text-dim hover:text-white text-sm border border-border-dark px-4 py-2">
                  <span className="material-symbols-outlined text-lg">filter_list</span>
                  Filters ({filteredClasses.length}/{totalCount})
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 p-0 pt-10 overflow-y-auto bg-[#0c1a15]">
                <ClassSidebar {...sidebarProps} />
              </SheetContent>
            </Sheet>
          </div>

          {/* Page header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4 border-b border-border-dark pb-4">
            <div>
              <h2 className="text-3xl md:text-4xl font-black text-white uppercase tracking-tighter mb-1 font-display">
                Class Intelligence
              </h2>
              <p className="text-slate-500 font-mono text-xs uppercase tracking-widest">
                Target Database // Zone A-7
              </p>
            </div>
            <div className="flex gap-4">
              <div className="flex items-center gap-2 text-xs font-mono uppercase text-slate-500">
                <span className="w-2 h-2 bg-danger block" /> Hazardous
              </div>
              <div className="flex items-center gap-2 text-xs font-mono uppercase text-slate-500">
                <span className="w-2 h-2 bg-primary block" /> Safe
              </div>
            </div>
          </div>

          {/* Card grid */}
          <ClassGrid classes={filteredClasses} />

          {/* Load more placeholder */}
          {filteredClasses.length > 0 && (
            <div className="flex justify-center mt-12 mb-8">
              <button className="flex items-center gap-2 px-8 py-3 border border-border-dark hover:bg-primary/10 hover:text-primary hover:border-primary transition-all text-sm font-mono uppercase tracking-widest text-slate-500">
                <span>Showing {filteredClasses.length} of {totalCount}</span>
              </button>
            </div>
          )}
        </section>
      </ScrollArea>
    </div>
  );
}
