import { useEffect, useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Activity,
  Bot,
  Brain,
  Camera,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  Cpu,
  Database,
  Eye,
  FileText,
  GitBranch,
  Globe,
  Layers,
  LayoutDashboard,
  Maximize2,
  MessageSquareText,
  Mic,
  Minus,
  Network,
  ScanText,
  Settings,
  ShieldCheck,
  Sparkles,
  Terminal,
  Waypoints,
  Wrench,
  X,
  Zap
} from 'lucide-react';
import AmbientCapsuleHUD from '../components/AmbientCapsuleHUD.jsx';
import { useBackend } from '../context/BackendContext.jsx';

export default function AppLayout() {
  const { apiClient, loginDemo, username } = useBackend();
  const navigate = useNavigate();
  const location = useLocation();

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

  function summonJarvisOrb() {
    if (window.secondBrain?.showOrb) {
      window.secondBrain.showOrb();
    }
  }

  const navTabs = [
    { label: 'Command Center', path: '/', icon: LayoutDashboard },
    { label: 'AI Partner', path: '/chat', icon: MessageSquareText },
    { label: 'Knowledge Graph', path: '/knowledge-graph', icon: Network },
    { label: 'Semantic Memory', path: '/semantic', icon: Brain },
    { label: 'Screen OCR', path: '/ocr', icon: ScanText },
    { label: 'Live Activity', path: '/activity', icon: Activity },
    { label: 'Memory Timeline', path: '/timeline', icon: Waypoints },
    { label: 'Voice Intercom', path: '/voice', icon: Mic },
    { label: 'Settings', path: '/settings', icon: Settings }
  ];

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#030712] text-slate-100 font-sans select-none relative">
      {/* ================= TOP FUTURISTIC STARK HUD HEADER ================= */}
      <header className="drag-region flex h-10 w-full shrink-0 items-center justify-between border-b border-cyan-500/20 bg-gradient-to-r from-slate-950 via-[#050b18] to-slate-950 px-3 text-xs backdrop-blur-2xl z-40">
        {/* Left: Stark AI OS Identity */}
        <div className="flex items-center gap-2.5 -webkit-app-region-no-drag">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-400/15 border border-cyan-400/50 text-cyan-300 shadow-[0_0_12px_rgba(56,189,248,0.5)]">
            <Cpu size={12} className="animate-pulse" />
          </div>
          <span className="font-mono text-[11px] font-bold tracking-widest text-cyan-300 uppercase">
            JARVIS // PERSONAL AI OPERATING SYSTEM
          </span>
          <span className="rounded bg-cyan-500/15 border border-cyan-400/30 px-1.5 py-0.2 text-[9px] font-mono text-cyan-300 font-semibold uppercase">
            MARK VII
          </span>
        </div>

        {/* Center: Top Navigation Pills */}
        <nav className="hidden md:flex items-center gap-1 -webkit-app-region-no-drag">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = location.pathname === tab.path;
            return (
              <NavLink
                key={tab.path}
                to={tab.path}
                className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-medium transition ${
                  isActive
                    ? 'border border-cyan-400/40 bg-cyan-500/15 text-cyan-300 shadow-[0_0_10px_rgba(56,189,248,0.25)] font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon size={12} className={isActive ? 'text-cyan-300' : 'text-slate-500'} />
                <span>{tab.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Right: Immanuel Profile & Window Controls */}
        <div className="flex items-center gap-2 -webkit-app-region-no-drag">
          <button
            type="button"
            onClick={summonJarvisOrb}
            className="flex items-center gap-1 rounded-full border border-amber-400/40 bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-mono font-bold text-amber-300 hover:bg-amber-500/20 transition shadow-[0_0_10px_rgba(251,191,36,0.2)]"
            title="Summon Golden Holographic Orb (Alt + J)"
          >
            <Sparkles size={11} className="text-amber-400 animate-spin" />
            <span>ALT + J</span>
          </button>

          <div className="flex items-center gap-1.5 rounded-lg border border-white/5 bg-white/5 px-2.5 py-0.5 text-[11px] font-mono text-slate-300">
            <span className="text-cyan-400 font-bold uppercase">{username || 'IMMANUEL'}</span>
            <span className="text-slate-600">/</span>
            <span className="text-[10px] text-emerald-400 font-bold">OPERATOR</span>
          </div>

          <div className="flex items-center border-l border-white/10 pl-1.5">
            <button
              type="button"
              onClick={minimize}
              className="flex h-6 w-7 items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition rounded"
              title="Minimize"
            >
              <Minus size={12} />
            </button>
            <button
              type="button"
              onClick={maximize}
              className="flex h-6 w-7 items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition rounded"
              title="Maximize"
            >
              <Maximize2 size={11} />
            </button>
            <button
              type="button"
              onClick={closeApp}
              className="flex h-6 w-7 items-center justify-center text-slate-400 hover:bg-red-600 hover:text-white transition rounded"
              title="Close"
            >
              <X size={13} />
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
