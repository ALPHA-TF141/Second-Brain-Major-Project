import { Bookmark, Folder, HelpCircle, Network, Search, Settings, Sparkles, LayoutGrid } from 'lucide-react';

export default function ObsidianRibbon({ activeView, onViewChange }) {
  const topButtons = [
    { id: 'files', title: 'Files & Folders', icon: Folder },
    { id: 'search', title: 'Search in all notes', icon: Search },
    { id: 'bookmarks', title: 'Bookmarks', icon: Bookmark },
    { id: 'graph', title: 'Open Graph view', icon: Network },
    { id: 'canvas', title: 'Create new canvas', icon: LayoutGrid },
  ];

  function summonJarvisOrb() {
    if (window.secondBrain?.showOrb) {
      window.secondBrain.showOrb();
    }
  }

  return (
    <div className="obsidian-ribbon flex h-full w-11 flex-col items-center justify-between py-2 text-[#737373] select-none z-20">
      {/* Top Tool Icons */}
      <div className="flex flex-col items-center gap-2">
        {topButtons.map((btn) => {
          const Icon = btn.icon;
          const isActive = activeView === btn.id;
          return (
            <button
              key={btn.id}
              type="button"
              onClick={() => onViewChange?.(btn.id)}
              className={`flex h-8 w-8 items-center justify-center rounded-md transition ${
                isActive
                  ? 'text-white bg-white/10'
                  : 'hover:text-slate-200 hover:bg-white/5'
              }`}
              title={btn.title}
            >
              <Icon size={17} />
            </button>
          );
        })}

        {/* Golden JARVIS AI Orb Summoner */}
        <button
          type="button"
          onClick={summonJarvisOrb}
          className="group relative flex h-8 w-8 items-center justify-center rounded-md bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 hover:text-amber-300 transition mt-1"
          title="Summon Golden JARVIS Holographic Orb (Alt + J)"
        >
          <Sparkles size={16} className="animate-spin text-amber-400" />
          <span className="absolute -top-1 -right-1 flex h-2 w-2 rounded-full bg-amber-400 animate-ping" />
        </button>
      </div>

      {/* Bottom Settings & Help */}
      <div className="flex flex-col items-center gap-1.5">
        <button
          type="button"
          onClick={() => onViewChange?.('settings')}
          className={`flex h-8 w-8 items-center justify-center rounded-md transition ${
            activeView === 'settings' ? 'text-white bg-white/10' : 'hover:text-slate-200 hover:bg-white/5'
          }`}
          title="Settings"
        >
          <Settings size={16} />
        </button>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-md hover:text-slate-200 hover:bg-white/5 transition"
          title="About Second Brain"
        >
          <HelpCircle size={16} />
        </button>
      </div>
    </div>
  );
}
