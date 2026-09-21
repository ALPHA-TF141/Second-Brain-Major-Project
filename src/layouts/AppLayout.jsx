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
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

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

  const primaryModules = [
    { label: 'Command Center', path: '/', icon: LayoutDashboard, badge: 'Core' },
    { label: 'AI Conversational Partner', path: '/chat', icon: MessageSquareText },
    { label: 'Knowledge Graph Network', path: '/knowledge-graph', icon: Network },
    { label: 'Semantic Memory Vectors', path: '/semantic', icon: Brain },
    { label: 'Screen OCR & Cognition', path: '/ocr', icon: ScanText },
    { label: 'Live Telemetry & Viewfinder', path: '/activity', icon: Activity },
    { label: 'Cognitive Memory Timeline', path: '/timeline', icon: Waypoints },
    { label: 'Spoken Voice Companion', path: '/voice', icon: Mic },
    { label: 'System Configuration', path: '/settings', icon: Settings }
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

        {/* Center: Live Neural Pulse Beacon */}
        <div className="hidden md:flex items-center gap-2 text-[10px] font-mono text-slate-400 uppercase tracking-wider">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-slate-300 font-medium">NEURAL CORTEX: ONLINE</span>
          <span className="text-slate-600">·</span>
          <span className="text-cyan-400 font-medium">EPHEMERAL ZERO-STORAGE ACTIVE</span>
          <span className="text-slate-600">·</span>
          <button
            type="button"
            onClick={summonJarvisOrb}
            className="flex items-center gap-1 text-amber-300 hover:text-amber-200 transition"
            title="Summon Golden Holo-Orb"
          >
            <Sparkles size={11} className="text-amber-400 animate-spin" />
            <span>ORB: ALT+J</span>
          </button>
        </div>

        {/* Right: Immanuel User Badge & Window Controls */}
        <div className="flex items-center gap-2 -webkit-app-region-no-drag">
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

      {/* ================= MAIN DUAL-PANE COGNITIVE SHELL ================= */}
      <div className="flex flex-1 min-h-0 min-w-0 overflow-hidden relative">
        {/* Left Modular Navigation Rail (Collapsible) */}
        <aside
          className={`flex flex-col justify-between border-r border-cyan-500/15 bg-slate-950/80 backdrop-blur-2xl transition-all duration-300 z-30 ${
            isSidebarCollapsed ? 'w-14' : 'w-64'
          }`}
        >
          {/* Top Header inside Sidebar */}
          <div>
            <div className="flex items-center justify-between border-b border-white/5 px-3 py-2.5">
              {!isSidebarCollapsed && (
                <div className="flex items-center gap-2">
                  <Compass size={14} className="text-cyan-400" />
                  <span className="text-[11px] font-mono font-bold tracking-wider text-slate-300 uppercase">
                    AI Modules
                  </span>
                </div>
              )}
              <button
                type="button"
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className={`p-1 text-slate-400 hover:text-white hover:bg-white/10 rounded transition ${
                  isSidebarCollapsed ? 'mx-auto' : ''
                }`}
                title={isSidebarCollapsed ? 'Expand Navigation' : 'Collapse Navigation'}
              >
                {isSidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
              </button>
            </div>

            {/* Navigation Items */}
            <nav className="p-2 space-y-1">
              {primaryModules.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    title={isSidebarCollapsed ? item.label : undefined}
                    className={`group flex items-center gap-3 rounded-xl px-2.5 py-2 text-xs font-medium transition-all ${
                      isActive
                        ? 'border border-cyan-400/40 bg-gradient-to-r from-cyan-500/20 to-blue-600/10 text-white shadow-[0_0_15px_rgba(56,189,248,0.25)] font-semibold'
                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                    } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                  >
                    <Icon size={16} className={isActive ? 'text-cyan-300' : 'text-slate-500 group-hover:text-slate-300'} />
                    {!isSidebarCollapsed && (
                      <span className="truncate flex-1">{item.label}</span>
                    )}
                    {!isSidebarCollapsed && item.badge && (
                      <span className="rounded bg-cyan-400/15 border border-cyan-400/30 px-1.5 py-0.2 text-[9px] font-mono font-bold text-cyan-300">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Bottom Telemetry Chip in Sidebar */}
          <div className="border-t border-white/5 p-2.5">
            {!isSidebarCollapsed ? (
              <div className="rounded-xl border border-white/5 bg-black/40 p-2.5 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>STORAGE BLOAT</span>
                  <span className="text-emerald-400 font-bold">0.0 MB</span>
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                  <span>GIT VAULT</span>
                  <span className="text-cyan-400 font-bold">SYNCED</span>
                </div>
              </div>
            ) : (
              <div className="flex justify-center text-emerald-400" title="Zero Local Storage Bloat Active">
                <ShieldCheck size={16} />
              </div>
            )}
          </div>
        </aside>

        {/* Main Application Viewport */}
        <div className="relative flex flex-1 flex-col min-h-0 min-w-0 overflow-hidden bg-[#030712]">
          <Outlet />
        </div>
      </div>

      {/* Global Ambient Floating Jarvis Orb Trigger (Alt + J / Alt + Space) */}
      <AmbientCapsuleHUD />
    </div>
  );
}
