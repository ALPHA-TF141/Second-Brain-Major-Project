import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Activity, Cpu, Minus, Maximize2, X, ShieldCheck, Sparkles, Terminal } from 'lucide-react';
import AmbientCapsuleHUD from '../components/AmbientCapsuleHUD.jsx';
import { useBackend } from '../context/BackendContext.jsx';

export default function AppLayout() {
  const { apiClient, loginDemo, username } = useBackend();

  // Auto-login as Immanuel & auto-start capture
  useEffect(() => {
    let cancelled = false;

    async function boot() {
      try {
        if (!apiClient.getToken()) await loginDemo('Immanuel');
        const status = await apiClient.captureStatus().catch(() => null);
        if (!cancelled && status && !status.is_active) {
          await apiClient.startCapture({
            sessionType: 'continuous',
            screenshotIntervalSeconds: 5
          }).catch((e) => console.warn('Auto-capture start note:', e));
        }
      } catch (e) {
        console.warn('Boot note:', e);
      }
    }

    boot();

    const handleCapture = (cmd) => {
      if (cmd === 'pause') apiClient.pauseCapture().catch(() => {});
      else if (cmd === 'resume') apiClient.resumeCapture().catch(() => {});
    };
    const ipc = window.secondBrain;
    if (ipc?.onCaptureCommand) {
      ipc.onCaptureCommand(handleCapture);
    }

    return () => { cancelled = true; };
  }, [apiClient, loginDemo]);

  function minimize() { window.secondBrain?.minimize?.(); }
  function maximize() { window.secondBrain?.maximize?.(); }
  function closeApp() { window.secondBrain?.close?.(); }

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#030712] text-slate-100 font-sans select-none relative">
      {/* Top Futuristic Stark HUD Bar */}
      <header className="drag-region flex h-10 w-full shrink-0 items-center justify-between border-b border-cyan-500/20 bg-gradient-to-r from-slate-950 via-[#050b18] to-slate-950 px-4 text-xs backdrop-blur-2xl z-40">
        {/* Left: Stark Industries Emblem */}
        <div className="flex items-center gap-2.5 -webkit-app-region-no-drag">
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-400/15 border border-cyan-400/50 text-cyan-300 shadow-[0_0_10px_rgba(56,189,248,0.5)]">
            <Cpu size={11} className="animate-pulse" />
          </div>
          <span className="font-mono text-[11px] font-bold tracking-widest text-cyan-300 uppercase">
            STARK INDUSTRIES // MARK VII OS
          </span>
        </div>

        {/* Center: Live Jarvis Neural Pulse */}
        <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono text-slate-400 uppercase tracking-wider">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-slate-300">JARVIS COGNITIVE CORE: ONLINE</span>
          <span className="text-slate-600">·</span>
          <span className="text-cyan-400">EPHEMERAL ZERO-STORAGE ACTIVE</span>
        </div>

        {/* Right: Immanuel Profile & Window Controls */}
        <div className="flex items-center gap-3 -webkit-app-region-no-drag">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-300">
            <span className="text-cyan-400 font-bold">{username || 'IMMANUEL'}</span>
            <span className="text-slate-600">/</span>
            <span className="text-[10px] text-emerald-400">ADMIN</span>
          </div>

          <div className="ml-2 flex items-center border-l border-white/10 pl-2">
            <button
              type="button"
              onClick={minimize}
              className="flex h-7 w-8 items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition"
              title="Minimize"
            >
              <Minus size={13} />
            </button>
            <button
              type="button"
              onClick={maximize}
              className="flex h-7 w-8 items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition"
              title="Maximize"
            >
              <Maximize2 size={12} />
            </button>
            <button
              type="button"
              onClick={closeApp}
              className="flex h-7 w-8 items-center justify-center text-slate-400 hover:bg-red-600 hover:text-white transition"
              title="Close"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Full-Bleed HUD Viewport */}
      <main className="relative flex flex-1 flex-col min-h-0 min-w-0 overflow-hidden bg-[#030712]">
        <Outlet />
      </main>

      {/* Ambient Floating Jarvis HUD Capsule (Alt + J / Alt + Space) */}
      <AmbientCapsuleHUD />
    </div>
  );
}
