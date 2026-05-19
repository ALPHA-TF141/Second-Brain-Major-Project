import { DatabaseZap, LogIn, RefreshCw } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

const statusStyles = {
  checking: 'border-warningGlow/30 bg-warningGlow/10 text-warningGlow',
  offline: 'border-red-400/30 bg-red-500/10 text-red-300',
  online: 'border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow',
  authenticated: 'border-mintGlow/30 bg-mintGlow/10 text-mintGlow'
};

function BackendStatus() {
  const { apiStatus, socketStatus, username, checkHealth, loginDemo } = useBackend();

  return (
    <section className="glass-panel rounded-lg p-5">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <DatabaseZap size={22} className="text-cyanGlow" />
          <div>
            <h3 className="font-semibold">Backend Connection</h3>
            <p className="text-sm text-slate-500">FastAPI, SQLite, JWT, and WebSocket foundation.</p>
          </div>
        </div>
        <span className={`rounded-lg border px-3 py-1 text-xs font-semibold ${statusStyles[apiStatus]}`}>
          API {apiStatus}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase text-slate-500">User</p>
          <p className="mt-1 text-sm font-semibold">{username || 'Not logged in'}</p>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase text-slate-500">WebSocket</p>
          <p className="mt-1 text-sm font-semibold">{socketStatus}</p>
        </div>
        <div className="flex gap-2 rounded-lg border border-white/10 bg-white/5 p-3">
          <button
            type="button"
            onClick={checkHealth}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10"
          >
            <RefreshCw size={15} />
            Check
          </button>
          <button
            type="button"
            onClick={loginDemo}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-cyanGlow px-3 py-2 text-sm font-bold text-slate-950 transition hover:bg-cyan-300"
          >
            <LogIn size={15} />
            Login
          </button>
        </div>
      </div>
    </section>
  );
}

export default BackendStatus;
