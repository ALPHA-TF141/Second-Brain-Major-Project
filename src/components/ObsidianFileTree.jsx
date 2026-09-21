import { useState } from 'react';
import { ChevronDown, ChevronRight, FilePlus, FolderPlus, ArrowUpDown, ChevronsDownUp, Search, Bookmark, Brain, Settings, FileText } from 'lucide-react';

export default function ObsidianFileTree({ onSelectCategory, activeCategory }) {
  const [openFolders, setOpenFolders] = useState({
    'Artificial Intelligence': true,
    'Cybersecurity': false,
    'Research Hub': false,
    'Daily Logs': false,
    'Articles': false,
    'META': true,
  });

  const toggleFolder = (folderName) => {
    setOpenFolders(prev => ({ ...prev, [folderName]: !prev[folderName] }));
  };

  const folders = [
    'African American Da...',
    'Article Notes',
    'Articles',
    'Artificial Intelligence',
    'Books',
    'Cases',
    'Clippings',
    'Codecademy',
    'Content',
    'copilot',
    'Coursera AI Foundati...',
    'Cyber',
    'Cybersecurity',
    'Cybersecurity Plans',
    'Daily Logs',
    'Daily To Do',
    'Epstein Files',
    'Excalidraw',
    'Films',
    'Guides',
    'History',
    'Images',
    'Instagram',
    'Intelligence Interaction',
    'Legal Cases',
    'Medical Conditions'
  ];

  const metaItems = [
    'Meta Index',
    'Structured Knowl...',
    'Meta Learning',
    'Journey - Obsidian'
  ];

  return (
    <div className="obsidian-sidebar flex h-full w-[240px] flex-col text-[#b3b3b3] select-none text-[11.5px] border-r border-[#262626]">
      {/* Top File Explorer Action Icons (Obsidian Style) */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#262626] text-slate-500">
        <div className="flex items-center gap-1.5">
          <button type="button" className="p-1 hover:text-white rounded hover:bg-white/5 transition" title="New note">
            <FilePlus size={14} />
          </button>
          <button type="button" className="p-1 hover:text-white rounded hover:bg-white/5 transition" title="New folder">
            <FolderPlus size={14} />
          </button>
          <button type="button" className="p-1 hover:text-white rounded hover:bg-white/5 transition" title="Change sort order">
            <ArrowUpDown size={14} />
          </button>
          <button type="button" className="p-1 hover:text-white rounded hover:bg-white/5 transition" title="Collapse all">
            <ChevronsDownUp size={14} />
          </button>
        </div>
      </div>

      {/* Vault Tree Items (Exact list from user's screenshot) */}
      <div className="thin-scrollbar flex-1 overflow-y-auto px-1 py-1.5 space-y-0.5">
        {folders.map((folderName) => {
          const isOpen = openFolders[folderName];
          const isSelected = activeCategory === folderName;

          return (
            <div key={folderName} className="space-y-0.5">
              <div
                onClick={() => {
                  toggleFolder(folderName);
                  onSelectCategory?.(folderName);
                }}
                className={`flex cursor-pointer items-center gap-1 rounded px-1.5 py-1 transition ${
                  isSelected ? 'bg-white/10 text-white font-medium' : 'hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                {isOpen ? (
                  <ChevronDown size={12} className="text-slate-500 shrink-0" />
                ) : (
                  <ChevronRight size={12} className="text-slate-500 shrink-0" />
                )}
                <span className="truncate">{folderName}</span>
              </div>

              {isOpen && folderName === 'Artificial Intelligence' && (
                <div className="ml-4 pl-1 border-l border-white/5 space-y-0.5">
                  {['Self-Improving Brain', 'GraphRAG Synthesis', 'Local Qwen 2.5', 'ChromaDB Vectors'].map((item) => (
                    <div
                      key={item}
                      onClick={() => onSelectCategory?.(item)}
                      className="flex cursor-pointer items-center gap-1.5 rounded px-2 py-0.5 text-[11px] text-slate-400 hover:text-white hover:bg-white/5 transition truncate"
                    >
                      <FileText size={10} className="text-slate-500 shrink-0" />
                      <span className="truncate">{item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Lower META Section matching screenshot */}
        <div className="pt-3 border-t border-white/5 space-y-1">
          <div className="flex items-center gap-2 px-2 text-slate-500 text-[11px] mb-1">
            <Search size={12} />
            <Bookmark size={12} />
          </div>

          <div
            onClick={() => toggleFolder('META')}
            className="flex cursor-pointer items-center gap-1 px-1.5 py-1 text-slate-400 font-semibold text-[11px] hover:text-white"
          >
            {openFolders['META'] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            <span>META</span>
          </div>

          {openFolders['META'] && (
            <div className="ml-4 pl-1 border-l border-white/5 space-y-0.5">
              {metaItems.map((item) => (
                <div
                  key={item}
                  onClick={() => onSelectCategory?.(item)}
                  className="flex cursor-pointer items-center gap-1.5 rounded px-2 py-0.5 text-[11px] text-slate-400 hover:text-white hover:bg-white/5 transition truncate"
                >
                  <FileText size={10} className="text-slate-500 shrink-0" />
                  <span className="truncate">{item}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Status Bar matching screenshot ("Brain") */}
      <div className="px-3 py-2 border-t border-[#262626] bg-[#141414] text-[10px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Brain size={13} className="text-cyan-400" />
          <span className="font-semibold text-slate-300">Brain</span>
        </div>
        <Settings size={12} className="text-slate-500 hover:text-white cursor-pointer" />
      </div>
    </div>
  );
}
