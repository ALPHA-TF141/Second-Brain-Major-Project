import { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Folder, FolderOpen, Hash, Layers, Search, Sparkles } from 'lucide-react';

export default function ObsidianFileTree({ onSelectCategory, activeCategory }) {
  const [openFolders, setOpenFolders] = useState({
    'Artificial Intelligence': true,
    'Cybersecurity': true,
    'Research Hub': true,
    'Daily Logs': false,
    'Articles': false,
  });

  const toggleFolder = (folderName) => {
    setOpenFolders(prev => ({ ...prev, [folderName]: !prev[folderName] }));
  };

  const categories = [
    { name: 'Research Hub', count: 18, items: ['Quantum Qubit Topology', 'LLM Memory Architecture', 'GraphRAG Ingestion', 'arXiv Summaries'] },
    { name: 'Artificial Intelligence', count: 34, items: ['Transformer Architecture', 'Self-Improving Second Brain', 'Ollama Local Serving', 'Vision Language Models'] },
    { name: 'Cybersecurity', count: 14, items: ['Network Threat Defense', 'Kernel Isolation', 'Zero-Knowledge Proofs', 'Cryptographic Hashing'] },
    { name: 'Articles & Web Intel', count: 26, items: ['YouTube Video Transcripts', 'Nature Research Briefings', 'Twitter / X Threads', 'HackerNews Discussions'] },
    { name: 'Daily Logs', count: 12, items: ['September 18 - System Sync', 'September 17 - Ingestion', 'September 16 - Architecture'] },
    { name: 'Guides & Cheatsheets', count: 8, items: ['FastAPI Microservices', 'React 18 Flow Engine', 'NVIDIA CUDA Acceleration'] },
    { name: 'Master To-Do', count: 5, items: ['Review faculty proposal', 'Run benchmark evaluation', 'Test mobile cloud vault'] },
  ];

  return (
    <div className="flex h-full w-64 flex-col bg-[#161616] text-[#b3b3b3] border-r border-[#262626] select-none text-xs">
      {/* Top Obsidian File Explorer Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-[#262626]">
        <div className="flex items-center gap-2">
          <Layers size={14} className="text-cyan-400" />
          <span className="font-semibold text-slate-200 tracking-wide uppercase text-[11px]">Vault Explorer</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">Immanuel's Vault</span>
      </div>

      {/* Vault Tree Items */}
      <div className="thin-scrollbar flex-1 overflow-y-auto px-1 py-2 space-y-0.5">
        {categories.map((cat) => {
          const isOpen = openFolders[cat.name];
          const isSelected = activeCategory === cat.name;

          return (
            <div key={cat.name} className="space-y-0.5">
              {/* Folder Row */}
              <div
                onClick={() => {
                  toggleFolder(cat.name);
                  onSelectCategory?.(cat.name);
                }}
                className={`flex cursor-pointer items-center justify-between rounded px-2 py-1.5 transition ${
                  isSelected ? 'bg-white/10 text-white font-medium' : 'hover:bg-white/5 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-1.5 truncate">
                  {isOpen ? <ChevronDown size={13} className="text-slate-400" /> : <ChevronRight size={13} className="text-slate-400" />}
                  {isOpen ? <FolderOpen size={13} className="text-cyan-400" /> : <Folder size={13} className="text-slate-400" />}
                  <span className="truncate">{cat.name}</span>
                </div>
                <span className="text-[10px] text-slate-600 font-mono">{cat.count}</span>
              </div>

              {/* Sub-items (Files) */}
              {isOpen && (
                <div className="ml-5 pl-1.5 border-l border-white/5 space-y-0.5">
                  {cat.items.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => onSelectCategory?.(item)}
                      className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-[11px] text-slate-400 hover:bg-white/5 hover:text-slate-200 transition truncate"
                    >
                      <FileText size={11} className="text-slate-500 shrink-0" />
                      <span className="truncate">{item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom Obsidian Status Info */}
      <div className="p-2.5 border-t border-[#262626] bg-[#141414] text-[10px] text-slate-500 flex items-center justify-between">
        <span>Git Vault Synced</span>
        <span className="text-cyan-400 font-mono">117 Notes</span>
      </div>
    </div>
  );
}
