import { ArrowLeft, ArrowRight, ChevronDown, Columns, Maximize2, Minus, Network, Plus, X, Pin } from 'lucide-react';

export default function ObsidianTabBar({ activeTab, onTabChange, onCloseTab }) {
  const tabs = [
    { id: 'todo', title: 'Master To-Do', pinned: true },
    { id: 'research', title: 'Research Hub', pinned: true },
    { id: 'focus', title: 'Current Main Focus Topics', pinned: true },
    { id: 'hotkeys', title: 'Hotkeys Guide', pinned: false },
    { id: 'daily', title: 'january 9', pinned: false },
    { id: 'graph', title: 'Graph view', icon: Network, pinned: false },
  ];

  function minimize() { window.secondBrain?.minimize?.(); }
  function maximize() { window.secondBrain?.maximize?.(); }
  function closeApp() { window.secondBrain?.close?.(); }

  return (
    <div className="obsidian-tabbar drag-region flex h-9 w-full items-center justify-between text-[#8c8c8c] select-none pl-1">
      {/* Left: History Nav & Open Tabs */}
      <div className="flex h-full items-center overflow-x-auto thin-scrollbar">
        {/* Navigation History Arrows */}
        <div className="flex items-center gap-0.5 px-1.5 -webkit-app-region-no-drag">
          <button type="button" className="p-1 hover:text-white rounded hover:bg-white/5 transition" title="Back">
            <ArrowLeft size={13} />
          </button>
          <button type="button" className="p-1 hover:text-white rounded hover:bg-white/5 transition" title="Forward">
            <ArrowRight size={13} />
          </button>
        </div>

        {/* Tab Items */}
        <div className="flex h-full items-end gap-0.5">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;

            return (
              <div
                key={tab.id}
                onClick={() => onTabChange?.(tab.id)}
                className={`group flex h-8 max-w-[190px] cursor-pointer items-center gap-1.5 rounded-t-md px-2.5 text-xs transition border-r border-[#262626] -webkit-app-region-no-drag ${
                  isActive
                    ? 'obsidian-active-tab text-slate-100 font-medium'
                    : 'bg-[#181818] text-[#8c8c8c] hover:bg-[#202020] hover:text-slate-300'
                }`}
              >
                {tab.pinned && <Pin size={10} className="text-slate-500 shrink-0" />}
                {Icon && <Icon size={12} className={isActive ? 'text-cyan-400' : 'text-slate-500'} />}
                <span className="truncate">{tab.title}</span>

                {!tab.pinned && (
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); onCloseTab?.(tab.id); }}
                    className="ml-1 rounded p-0.5 text-slate-500 opacity-0 group-hover:opacity-100 hover:text-white hover:bg-white/10 transition"
                  >
                    <X size={11} />
                  </button>
                )}
              </div>
            );
          })}

          {/* New Tab Button */}
          <button
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded hover:bg-white/10 hover:text-white transition -webkit-app-region-no-drag ml-1 mb-0.5"
            title="New tab"
          >
            <Plus size={13} />
          </button>
        </div>
      </div>

      {/* Right: Window Controls & Tools */}
      <div className="flex items-center gap-1 -webkit-app-region-no-drag pr-2">
        <button type="button" className="p-1.5 hover:text-white rounded hover:bg-white/5 transition" title="Split right">
          <Columns size={13} />
        </button>
        <button type="button" className="p-1.5 hover:text-white rounded hover:bg-white/5 transition" title="More options">
          <ChevronDown size={13} />
        </button>

        {/* Electron Window Frameless Controls */}
        <div className="ml-2 flex items-center">
          <button
            type="button"
            onClick={minimize}
            className="flex h-7 w-9 items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition"
            title="Minimize"
          >
            <Minus size={13} />
          </button>
          <button
            type="button"
            onClick={maximize}
            className="flex h-7 w-9 items-center justify-center text-slate-400 hover:bg-white/10 hover:text-white transition"
            title="Maximize"
          >
            <Maximize2 size={12} />
          </button>
          <button
            type="button"
            onClick={closeApp}
            className="flex h-7 w-9 items-center justify-center text-slate-400 hover:bg-red-600 hover:text-white transition"
            title="Close"
          >
            <X size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
