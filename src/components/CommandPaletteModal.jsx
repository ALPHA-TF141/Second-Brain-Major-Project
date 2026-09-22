import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  CheckSquare,
  Bell,
  Mail,
  Network,
  Bot,
  Rocket,
  FileText,
  Calendar,
  ArrowRight
} from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

export default function CommandPaletteModal() {
  const { apiClient } = useBackend();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Keyboard shortcut Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await apiFetch(`${apiClient.baseUrl}/api/os/search?q=${encodeURIComponent(query.trim())}`);
        if (res.ok) {
          const data = await res.json();
          setResults(data.results || []);
        }
      } catch {
        //
      } finally {
        setIsSearching(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  const defaultCommands = [
    { title: 'Open Knowledge Graph', type: 'command', icon: Network, target: '/knowledge-graph' },
    { title: 'Open Full-Screen AI Agent', type: 'command', icon: Bot, target: '/agent' },
    { title: 'View Tasks & Directives', type: 'command', icon: CheckSquare, target: '/tasks' },
    { title: 'Open Gmail Workspace', type: 'command', icon: Mail, target: '/gmail' },
    { title: 'Open Calendar & Schedule', type: 'command', icon: Calendar, target: '/calendar' },
    { title: 'View Reminders', type: 'command', icon: Bell, target: '/reminders' },
    { title: 'Open Project Workspaces', type: 'command', icon: Rocket, target: '/projects' },
    { title: 'Browse Knowledge Base', type: 'command', icon: FileText, target: '/knowledge' },
  ];

  function handleSelect(item) {
    setIsOpen(false);
    setQuery('');
    if (item.target) {
      navigate(item.target);
    }
  }

  if (!isOpen) return null;

  return (
    <div
      onClick={() => setIsOpen(false)}
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/85 p-4 backdrop-blur-md select-none font-sans"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl overflow-hidden rounded-2xl border border-cyan-500/30 bg-[#0d111c] shadow-2xl backdrop-blur-2xl"
      >
        {/* Search Bar */}
        <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3 bg-black/40">
          <Search size={16} className="text-cyan-400 shrink-0" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across notes, tasks, emails, projects, files, and knowledge..."
            className="w-full bg-transparent text-xs text-white outline-none placeholder:text-slate-500 font-medium"
          />
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono">
            <span>ESC to close</span>
          </div>
        </div>

        {/* Results Stream */}
        <div className="max-h-80 overflow-y-auto thin-scrollbar p-2 space-y-1">
          {query.trim() && results.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold px-2 block">
                Universal Search Matches ({results.length})
              </span>
              {results.map((res, i) => (
                <div
                  key={i}
                  onClick={() => handleSelect(res)}
                  className="flex cursor-pointer items-center justify-between rounded-xl p-2.5 text-xs text-slate-200 hover:bg-cyan-500/15 hover:text-white transition"
                >
                  <div>
                    <h4 className="font-semibold text-white">{res.title}</h4>
                    <p className="text-[10px] text-slate-400 mt-0.5">{res.subtitle}</p>
                  </div>
                  <ArrowRight size={13} className="text-cyan-400" />
                </div>
              ))}
            </div>
          )}

          {query.trim() && results.length === 0 && !isSearching && (
            <div className="py-8 text-center text-xs text-slate-500">
              No matching knowledge entries or tasks found for "{query}".
            </div>
          )}

          {(!query.trim() || results.length === 0) && (
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-500 font-bold px-2 block">
                Quick Navigation & Commands
              </span>
              {defaultCommands.map((cmd, i) => {
                const Icon = cmd.icon;
                return (
                  <div
                    key={i}
                    onClick={() => handleSelect(cmd)}
                    className="flex cursor-pointer items-center justify-between rounded-xl p-2.5 text-xs text-slate-300 hover:bg-white/5 hover:text-white transition"
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon size={14} className="text-cyan-400" />
                      <span>{cmd.title}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">Open</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
