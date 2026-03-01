import { useNavigate } from 'react-router-dom';

const ERROR_LOGS = [
  'SIGINT_TIMEOUT: PACKET LOSS AT SECTOR 7G',
  'INVALID_PTR: 0x00045F2A IN MODULE_CORE',
  'SECTOR_NOT_FOUND: UNREACHABLE COORDINATES',
  'FATAL: HANDSHAKE FAILED WITH REMOTE NODE 44.12',
  'RETRYING AUTHENTICATION... DENIED',
];

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="bg-[#0a0e14] text-gray-300 font-display overflow-hidden h-screen flex flex-col">
      <header className="bg-[#151c27] border-b border-white/10 px-6 py-3 flex items-center justify-between z-50">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center">
            <span className="text-black font-bold text-xs">UT</span>
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-widest uppercase">
              UNTRASHIFY // SIGINT_OS
            </h1>
            <p className="text-[10px] text-primary/70 font-mono">
              ENCRYPTED CONNECTION: STABLE
            </p>
          </div>
        </div>
        <div className="flex items-center gap-6 text-[10px] font-mono">
          <div className="text-right hidden sm:block">
            <p className="text-white/50">OPERATOR: ALPHA-9</p>
            <p className="text-white">NODE: 192.168.0.244</p>
          </div>
          <div className="hidden sm:block h-8 w-px bg-white/10" />
          <div className="text-primary animate-pulse">[ SYSTEM ONLINE ]</div>
        </div>
      </header>

      <nav className="bg-[#151c27]/50 border-b border-white/5 px-6 py-2 flex items-center gap-8 text-[11px] font-bold tracking-tighter z-40">
        <span className="text-white/40">DIRECTORIES:</span>
        <button onClick={() => navigate('/')} className="hover:text-primary transition-colors">
          TERMINAL
        </button>
        <button onClick={() => navigate('/analytics')} className="hover:text-primary transition-colors">
          SATELLITE_LINK
        </button>
        <button onClick={() => navigate('/classes')} className="hover:text-primary transition-colors">
          DECRYPT_LOGS
        </button>
        <span className="hidden sm:inline hover:text-primary transition-colors cursor-pointer">
          THREAT_INTEL
        </span>
        <div className="ml-auto text-danger">ALERT: UNKNOWN_EXCEPTION_DETECTED</div>
      </nav>

      <main className="flex-1 relative flex flex-col items-center justify-center text-center p-4">
        <div className="absolute inset-0 overflow-hidden opacity-10 pointer-events-none select-none z-0">
          <div className="font-mono text-xs text-primary space-y-2 py-10 animate-scroll-logs">
            {[...ERROR_LOGS, ...ERROR_LOGS, ...ERROR_LOGS, ...ERROR_LOGS].map((log, i) => (
              <p key={i}>{log}</p>
            ))}
          </div>
        </div>

        <div className="z-10 relative max-w-2xl px-6">
          <h2 className="text-danger font-mono font-bold tracking-widest mb-4 text-sm sm:text-base">
            ERROR 404: ACCESS DENIED / RESOURCE NOT FOUND
          </h2>

          <div className="relative inline-block mb-8">
            <span className="text-[8rem] sm:text-[12rem] font-bold text-danger leading-none glitch-text select-none">
              404
            </span>
          </div>

          <div className="bg-black/40 border border-white/10 p-6 mb-10 backdrop-blur-sm">
            <p className="text-lg font-bold text-white mb-2 uppercase tracking-widest">
              UNAUTHORIZED ACCESS DETECTED.
            </p>
            <p className="text-sm text-white/60 mb-6 font-mono">
              The requested SIGINT coordinate could not be located in the current database.
              Your attempt has been logged. Return to secure terminal immediately.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="w-full sm:w-auto px-8 py-3 bg-primary text-black font-bold uppercase text-xs hover:bg-white transition-all duration-300 border-none"
              >
                Return to Dashboard
              </button>
              <button
                onClick={() => navigate(-1 as never)}
                className="w-full sm:w-auto px-8 py-3 bg-transparent border border-white/20 text-white font-bold uppercase text-xs hover:border-primary hover:text-primary transition-all duration-300"
              >
                Retry Connection
              </button>
              <button
                onClick={() => navigate('/analytics')}
                className="w-full sm:w-auto px-8 py-3 bg-transparent border border-white/20 text-white font-bold uppercase text-xs hover:border-danger hover:text-danger transition-all duration-300"
              >
                Report to Command
              </button>
            </div>
          </div>

          <div className="font-mono text-xs flex items-center justify-center gap-2">
            <span className="text-white/40">SYS_ADMIN@UNTRASHIFY:~$</span>
            <span className="text-primary">INPUT REQUIRED</span>
            <span className="w-2 h-4 bg-primary animate-blink" />
          </div>
        </div>
      </main>

      <footer className="bg-[#151c27]/80 border-t border-white/10 px-6 py-4 flex flex-col md:flex-row items-center justify-between text-[10px] text-white/40 font-mono z-50">
        <div className="flex gap-4">
          <span>LAT: 38.8977° N</span>
          <span>LONG: 77.0365° W</span>
          <span className="text-primary/60">STATUS: WARNING_MODE</span>
        </div>
        <div className="mt-2 md:mt-0 uppercase">
          © 2024 UNTRASHIFY MIL-SPEC SIGINT // CLASSIFIED TOP SECRET
        </div>
      </footer>
    </div>
  );
}
