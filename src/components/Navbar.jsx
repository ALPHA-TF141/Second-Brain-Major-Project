import { Bell, Maximize2, Minus, Power, X } from 'lucide-react';
import { useAssistant } from '../context/AssistantContext.jsx';
import { useIpcAppInfo } from '../hooks/useIpc.js';

function Navbar() {
  const appInfo = useIpcAppInfo();
  const { isAssistantRunning, toggleAssistant, notifications } = useAssistant();

  return (
    <header className="drag-region flex h-16 shrink-0 items-center justify-between border-b border-white/10 bg-slate-950/45 px-4 backdrop-blur-xl sm:px-6">
      <div>
        <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{appInfo.phase}</p>
        <h2 className="text-base font-semibold text-slate-100 sm:text-lg">{appInfo.name}</h2>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleAssistant}
          className={[
            'hidden items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition sm:flex',
            isAssistantRunning
              ? 'border-mintGlow/40 bg-mintGlow/10 text-mintGlow'
              : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
          ].join(' ')}
        >
          <Power size={16} />
          {isAssistantRunning ? 'Running' : 'Start'}
        </button>

        <div className="relative">
          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-300 transition hover:bg-white/10"
            aria-label="Notifications"
          >
            <Bell size={18} />
          </button>
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-cyanGlow px-1 text-xs font-bold text-slate-950">
            {notifications.length}
          </span>
        </div>

        <div className="ml-2 flex overflow-hidden rounded-lg border border-white/10">
          <button
            type="button"
            onClick={() => window.secondBrain?.minimize?.()}
            className="flex h-9 w-10 items-center justify-center bg-white/5 text-slate-400 transition hover:bg-white/10"
            aria-label="Minimize"
          >
            <Minus size={16} />
          </button>
          <button
            type="button"
            onClick={() => window.secondBrain?.maximize?.()}
            className="flex h-9 w-10 items-center justify-center bg-white/5 text-slate-400 transition hover:bg-white/10"
            aria-label="Maximize"
          >
            <Maximize2 size={15} />
          </button>
          <button
            type="button"
            onClick={() => window.secondBrain?.close?.()}
            className="flex h-9 w-10 items-center justify-center bg-white/5 text-slate-400 transition hover:bg-red-500/80 hover:text-white"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
