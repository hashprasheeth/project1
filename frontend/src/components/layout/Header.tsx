import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { useState } from 'react';

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Analytics', to: '/analytics' },
  { label: 'Classes', to: '/classes' },
] as const;

function NavLinkItem({ label, to, onClick }: { label: string; to: string; onClick?: () => void }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          'px-4 py-2 text-sm font-medium uppercase tracking-widest transition-colors',
          isActive
            ? 'text-primary bg-primary/10 border-b-2 border-primary font-bold'
            : 'text-slate-400 hover:text-white hover:bg-white/5'
        )
      }
    >
      {label}
    </NavLink>
  );
}

export default function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="h-14 shrink-0 flex items-center justify-between border-b border-border-dark bg-[#0d1117] px-4 md:px-6 z-20">
      <div className="flex items-center gap-4 text-primary">
        <span className="material-symbols-outlined text-[28px]">recycling</span>
        <h1 className="text-white text-lg font-bold tracking-widest font-display">
          UNTRASHIFY <span className="text-text-dim text-sm font-normal hidden sm:inline">v2.4</span>
        </h1>
      </div>

      {/* Desktop nav */}
      <nav className="hidden md:flex items-center gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLinkItem key={item.to} {...item} />
        ))}
      </nav>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-primary/10 border border-primary/20 text-primary text-xs font-bold tracking-wider">
          <span className="material-symbols-outlined text-[16px] animate-pulse">fiber_manual_record</span>
          LIVE FEED
        </div>
        <div className="hidden lg:flex items-center">
          <div className="bg-danger text-black px-4 py-1 text-sm font-bold tracking-widest clip-path-slant flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">warning</span>
            HAZARD LVL 3
          </div>
        </div>
        <div className="hidden md:flex items-center gap-3 border-l border-border-dark pl-4">
          <button className="text-text-dim hover:text-white transition-colors">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <button className="text-text-dim hover:text-white transition-colors">
            <span className="material-symbols-outlined">account_circle</span>
          </button>
        </div>

        {/* Mobile hamburger */}
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <button className="md:hidden text-text-dim hover:text-white">
              <span className="material-symbols-outlined">menu</span>
            </button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0 pt-14">
            <nav className="flex flex-col p-4 gap-2">
              {NAV_ITEMS.map((item) => (
                <NavLinkItem key={item.to} {...item} onClick={() => setMobileOpen(false)} />
              ))}
            </nav>
            <div className="mt-auto p-4 border-t border-border-dark flex flex-col gap-2">
              <button className="flex items-center gap-2 text-text-dim hover:text-white text-sm">
                <span className="material-symbols-outlined text-lg">settings</span>
                Settings
              </button>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  );
}
