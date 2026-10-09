import { useEffect, useState, useRef } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  Activity,
  FlaskConical,
  Bell,
  BookOpen,
  Bot,
  Calendar,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Clock,
  Cpu,
  Folder,
  LayoutDashboard,
  Link2,
  Mail,
  Maximize2,
  Minus,
  Network,
  Rocket,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  X,
  Zap
} from 'lucide-react';
import AmbientCapsuleHUD from '../components/AmbientCapsuleHUD.jsx';
import CommandPaletteModal from '../components/CommandPaletteModal.jsx';
import PitchingDashboardDrawer from '../components/PitchingDashboardDrawer.jsx';
import LiveConnectorsModal from '../components/LiveConnectorsModal.jsx';
import { useBackend } from '../context/BackendContext.jsx';

export default function AppLayout() {
  const { apiClient, loginDemo, username, liveEvents } = useBackend();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(isHome);
  const [isPitchDrawerOpen, setIsPitchDrawerOpen] = useState(false);
  const [isConnectorsModalOpen, setIsConnectorsModalOpen] = useState(false);
  const lastNotified = useRef(null);
  const lastWakedAt = useRef(null);
  const lastSpokenAt = useRef(null);

  /**
   * Hands-free: the backend raises `wake` when it hears "Hey Jarvis".
   * Bring the orb up so there is a face attached to the assistant that just
   * answered you. `revealOrb` always shows; `showOrb` would toggle it away if
   * it happened to already be visible.
   */
  useEffect(() => {
    const latest = (liveEvents || [])[0];
    if (!latest || latest.type !== 'wake') return;
    if (lastWakedAt.current === latest.timestamp) return;
    lastWakedAt.current = latest.timestamp;

    const bridge = typeof window !== 'undefined' ? window.secondBrain : null;
    if (bridge?.revealOrb) {
      bridge.revealOrb();
    } else if (bridge?.showOrb) {
      bridge.showOrb();
    }
  }, [liveEvents]);

  /**
   * Proactive voice: the backend decides WHAT is worth saying (priority gate,
   * quiet hours, cooldown, dedupe) and sends `speak`. The renderer only has to
   * open its mouth, so the policy lives in one place.
   */
  useEffect(() => {
    const latest = (liveEvents || [])[0];
    if (!latest || latest.type !== 'speak' || !latest.text) return;
    if (lastSpokenAt.current === latest.timestamp) return;
    lastSpokenAt.current = latest.timestamp;

    // A face for the voice.
    const bridge = typeof window !== 'undefined' ? window.secondBrain : null;
    if (latest.show_orb) {
      bridge?.revealOrb?.();
    }

    try {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(latest.text);
        utterance.rate = 1.02;
        utterance.pitch = 1.0;
        const voices = window.speechSynthesis.getVoices();
        const natural = voices.find(
          (v) => v.lang?.includes('en-GB') || v.name?.includes('Natural') || v.name?.includes('George')
        );
        if (natural) utterance.voice = natural;
        window.speechSynthesis.speak(utterance);
      }
    } catch {
      // Speech is a nicety; never let it break the shell.
    }
  }, [liveEvents]);

  /**
   * Surface mail-ingestion alerts as real OS notifications.
   *
   * The backend broadcasts a `mail_sync` event over /ws/live whenever an agent
   * pass ingests mail. In Electron the renderer can raise a native Windows
   * notification directly, so a deadline Jarvis found reaches the user even if
   * the window is buried.
   */
  useEffect(() => {
    const latest = (liveEvents || [])[0];
    if (!latest || latest.type !== 'mail_sync') return;
    if (lastNotified.current === latest.timestamp) return;
    lastNotified.current = latest.timestamp;

    const count = latest.ingested ?? 0;
    const actions = latest.actions ?? 0;
    if (!count) return;

    const title = actions
      ? `Jarvis: ${actions} new action item${actions > 1 ? 's' : ''}`
      : `Jarvis: ${count} new email${count > 1 ? 's' : ''} stored`;

    const body = `${latest.account || 'Mailbox'} - ${count} message${count > 1 ? 's' : ''} added to memory` +
      (actions ? `, ${actions} deadline${actions > 1 ? 's' : ''} detected.` : '.');

    try {
      if (typeof window !== 'undefined' && 'Notification' in window) {
        if (Notification.permission === 'granted') {
          new Notification(title, { body, silent: false });
        } else if (Notification.permission !== 'denied') {
          Notification.requestPermission().then((permission) => {
            if (permission === 'granted') new Notification(title, { body });
          });
        }
      }
    } catch {
      // notifications are a nicety - never let them break the shell
    }
  }, [liveEvents]);

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

  // All 15 required persistent primary working tabs
  const allWorkingTabs = [
    { label: 'Home', path: '/', icon: LayoutDashboard, badge: 'Live' },
    { label: 'AI Agent', path: '/agent', icon: Bot, badge: 'Qwen' },
    { label: 'Gmail', path: '/gmail', icon: Mail },
    { label: 'Calendar', path: '/calendar', icon: Calendar },
    { label: 'Tasks', path: '/tasks', icon: CheckSquare },
    { label: 'Notifications', path: '/notifications', icon: Bell },
    { label: 'Reminders', path: '/reminders', icon: Clock },
    { label: 'Knowledge', path: '/knowledge', icon: BookOpen },
    { label: 'Knowledge Graph', path: '/knowledge-graph', icon: Network },
    { label: 'Files', path: '/files', icon: Folder },
    { label: 'Projects', path: '/projects', icon: Rocket },
    { label: 'Automations', path: '/automations', icon: Zap },
    { label: 'Memory Lab', path: '/memory-lab', icon: FlaskConical },
    { label: 'Agent Activity', path: '/activity', icon: Activity },
    { label: 'Integrations', path: '/integrations', icon: Link2 },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#070a13] text-slate-100 font-sans select-none relative">
      {/* ================= TOP STARK HUD HEADER ================= */}
      <header className="drag-region flex h-10 w-full shrink-0 items-center justify-between border-b border-cyan-500/20 bg-gradient-to-r from-slate-950 via-[#0a0f24] to-slate-950 px-3 text-xs backdrop-blur-2xl z-40">
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

        {/* Center: Search & Quick Launcher Shortcut */}
        <div className="hidden md:flex items-center gap-2 text-[10px] font-mono text-slate-400 -webkit-app-region-no-drag">
          <div
            onClick={() => {
              window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }));
            }}
            className="flex cursor-pointer items-center gap-2 rounded-lg border border-white/10 bg-black/40 px-3 py-1 text-slate-400 hover:border-cyan-400/40 hover:text-white transition"
          >
            <Search size={11} className="text-cyan-400" />
            <span>Search & Commands</span>
            <kbd className="rounded bg-white/10 px-1.5 py-0.2 text-[9px] font-bold text-slate-300">Ctrl + K</kbd>
          </div>

          <button
            type="button"
            onClick={() => setIsPitchDrawerOpen(true)}
            className="flex items-center gap-1.5 rounded-lg border border-cyan-400/30 bg-cyan-500/10 px-2.5 py-1 text-cyan-300 hover:bg-cyan-500/20 transition font-bold"
            title="Pitching Intel Deck"
          >
            <Sparkles size={11} />
            <span>PITCH DECK</span>
          </button>

          <button
            type="button"
            onClick={() => setIsConnectorsModalOpen(true)}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-emerald-300 hover:bg-emerald-500/20 transition font-bold"
            title="Persistent DB App Connectors"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>CONNECTORS (DB)</span>
          </button>
        </div>

        {/* Right: Immanuel Profile & Window Controls */}
        <div className="flex items-center gap-2 -webkit-app-region-no-drag">
          <button
            type="button"
            onClick={summonJarvisOrb}
            className="flex items-center gap-1 rounded-full border border-amber-400/40 bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-mono font-bold text-amber-300 hover:bg-amber-500/20 transition shadow-[0_0_10px_rgba(251,191,36,0.2)]"
            title="Summon Golden Holographic Orb (Alt + J)"
          >
            <Sparkles size={11} className="text-amber-400 animate-spin" />
            <span>ORB: ALT+J</span>
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

      {/* ================= MAIN DUAL-PANE SHELL ================= */}
      <div className="flex flex-1 min-h-0 min-w-0 overflow-hidden relative">
        {/* Left Persistent Navigation Rail (All 15 Working Tabs Visible) */}
        <aside
          className={`flex flex-col justify-between border-r border-cyan-500/15 bg-slate-950/85 backdrop-blur-2xl transition-all duration-200 z-30 select-none ${
            isSidebarCollapsed ? 'w-14' : 'w-56'
          }`}
        >
          {/* Top Header inside Sidebar */}
          <div className="flex flex-col min-h-0 flex-1">
            <div className="flex items-center justify-between border-b border-white/5 px-3 py-2 shrink-0">
              {!isSidebarCollapsed && (
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  <span className="text-[10px] font-mono font-bold tracking-wider text-slate-400 uppercase">
                    Operating System
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

            {/* Navigation Tabs Stream */}
            <nav className="thin-scrollbar flex-1 overflow-y-auto p-1.5 space-y-0.5">
              {allWorkingTabs.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    title={isSidebarCollapsed ? item.label : undefined}
                    className={`group flex items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-xs font-medium transition ${
                      isActive
                        ? 'border border-cyan-400/40 bg-cyan-500/15 text-cyan-300 font-bold shadow-[0_0_12px_rgba(56,189,248,0.2)]'
                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                    } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                  >
                    <Icon size={15} className={isActive ? 'text-cyan-300' : 'text-slate-500 group-hover:text-slate-300'} />
                    {!isSidebarCollapsed && (
                      <span className="truncate flex-1">{item.label}</span>
                    )}
                    {!isSidebarCollapsed && item.badge && (
                      <span className="rounded bg-cyan-400/10 border border-cyan-400/20 px-1.5 py-0.2 text-[8.5px] font-mono font-bold text-cyan-300">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Bottom Telemetry Chip in Sidebar */}
          <div className="border-t border-white/5 p-2 shrink-0">
            {!isSidebarCollapsed ? (
              <div className="rounded-xl border border-white/5 bg-black/40 p-2 space-y-1">
                <div className="flex items-center justify-between text-[9.5px] font-mono text-slate-400">
                  <span>STORAGE</span>
                  <span className="text-emerald-400 font-bold">0.0 MB BLOAT</span>
                </div>
                <div className="flex items-center justify-between text-[9.5px] font-mono text-slate-400">
                  <span>GIT VAULT</span>
                  <span className="text-cyan-400 font-bold">AUTO 60s</span>
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
        <div className="relative flex flex-1 flex-col min-h-0 min-w-0 overflow-hidden bg-[#070a13]">
          <Outlet />
        </div>
      </div>

      {/* Global Ambient Floating Jarvis Orb Trigger (Alt + J / Alt + Space) */}
      <AmbientCapsuleHUD />

      {/* Global Universal Command Palette (Ctrl + K) */}
      <CommandPaletteModal />

      {/* Global Slide-Over Pitching Dashboard Drawer */}
      <PitchingDashboardDrawer
        isOpen={isPitchDrawerOpen}
        onClose={() => setIsPitchDrawerOpen(false)}
        onOpenConnectorsModal={() => {
          setIsPitchDrawerOpen(false);
          setIsConnectorsModalOpen(true);
        }}
      />

      {/* Global Persistent SQLite DB Connectors Modal */}
      <LiveConnectorsModal
        isOpen={isConnectorsModalOpen}
        onClose={() => setIsConnectorsModalOpen(false)}
      />
    </div>
  );
}
