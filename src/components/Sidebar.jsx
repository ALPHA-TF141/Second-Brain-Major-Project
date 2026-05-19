import { NavLink } from 'react-router-dom';
import {
  Activity,
  Bot,
  Brain,
  ScanText,
  LayoutDashboard,
  MessageSquareText,
  Mic2,
  Settings,
  Sparkles,
  Waypoints,
  Network
} from 'lucide-react';

const navItems = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'AI Chat', path: '/chat', icon: MessageSquareText },
  { label: 'Timeline', path: '/timeline', icon: Waypoints },
  { label: 'Live Activity', path: '/activity', icon: Activity },
  { label: 'OCR Knowledge', path: '/ocr', icon: ScanText },
  { label: 'Semantic Memory', path: '/semantic', icon: Brain },
  { label: 'Knowledge Graph', path: '/knowledge-graph', icon: Network },
  { label: 'Voice Assistant', path: '/voice', icon: Mic2 },
  { label: 'Settings', path: '/settings', icon: Settings }
];

function Sidebar() {
  return (
    <aside className="hidden h-full w-72 shrink-0 border-r border-white/10 bg-slate-950/45 px-4 py-5 backdrop-blur-xl lg:block">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 shadow-glow">
          <Bot size={22} className="text-cyanGlow" />
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-wide">Second Brain</h1>
          <p className="text-xs uppercase text-slate-500">Desktop AI shell</p>
        </div>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              [
                'group flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'border border-cyanGlow/30 bg-cyanGlow/12 text-white shadow-glow'
                  : 'text-slate-400 hover:bg-white/7 hover:text-slate-100'
              ].join(' ')
            }
          >
            <item.icon size={19} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="glass-panel mt-8 rounded-lg p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <Sparkles size={16} className="text-mintGlow" />
          Phase 9
        </div>
        <p className="text-sm leading-6 text-slate-400">
          Knowledge Graph engine with interactive visualization, recommendations, and learning path exploration.
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;
