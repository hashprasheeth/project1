import Header from './Header';
import SubHeader from './SubHeader';

interface AppShellProps {
  readonly children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex flex-col h-screen bg-background-dark overflow-hidden">
      <Header />
      <SubHeader />
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
