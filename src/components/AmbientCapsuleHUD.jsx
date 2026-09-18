import { useEffect, useRef, useState } from 'react';
import { Command, Cpu, Mic, Search, Sparkles, X, Zap, ArrowRight, CornerDownLeft } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { useNavigate } from 'react-router-dom';

export default function AmbientCapsuleHUD({ onTriggerBriefing }) {
  const { apiClient, liveEvents } = useBackend();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [proactiveAlert, setProactiveAlert] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [response, setResponse] = useState('');
  const inputRef = useRef(null);

  // Listen for Electron Global Hotkey (Alt + Space)
  useEffect(() => {
    const ipc = window.secondBrain;
    if (ipc?.onSpotlightToggle) {
      ipc.onSpotlightToggle(() => {
        setIsOpen((prev) => !prev);
      });
    }

    // Keyboard shortcut within browser window as well
    const handleKeyDown = (e) => {
      if ((e.altKey && e.code === 'Space') || (e.ctrlKey && e.code === 'Space')) {
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

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    } else {
      setQuery('');
      setResponse('');
    }
  }, [isOpen]);

  // Listen for Proactive Cognitive Collisions from WebSocket
  useEffect(() => {
    const insightEvent = liveEvents.find((e) => e.type === 'proactive_insight');
    if (insightEvent && insightEvent.data) {
      setProactiveAlert(insightEvent.data);
      const timer = setTimeout(() => setProactiveAlert(null), 12000);
      return () => clearTimeout(timer);
    }
  }, [liveEvents]);

  async function handleSearch(e) {
    e?.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setResponse('');
    try {
      const res = await apiClient.askMemory({ question: query.trim(), mode: 'summary' });
      setResponse(res.answer || 'Memory retrieved.');
    } catch {
      setResponse('Jarvis local reasoning active. Connect Ollama or configure LLM.');
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <>
      {/* Floating Proactive Toast Pill (Top Center) */}
      {proactiveAlert && !isOpen && (
        <div
          onClick={() => setIsOpen(true)}
          className="fixed top-3 left-1/2 -translate-x-1/2 z-40 flex cursor-pointer items-center gap-3 rounded-full border border-amber-400/50 bg-black/85 px-4 py-2 text-xs text-amber-200 shadow-glow backdrop-blur-xl transition hover:scale-105 animate-bounce"
        >
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-amber-300">
            <Zap size={13} />
          </div>
          <span className="font-semibold">{proactiveAlert.title}</span>
          <span className="text-[11px] text-slate-400">Press Alt+Space to inspect &rarr;</span>
        </div>
      )}

      {/* Floating Ambient Capsule Button */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="group fixed bottom-5 right-5 z-40 flex items-center gap-2.5 rounded-full border border-cyanGlow/40 bg-slate-950/90 px-4 py-2.5 text-xs font-bold text-slate-200 shadow-glow backdrop-blur-xl transition hover:border-cyanGlow hover:scale-105"
      >
        <span className="flex h-2 w-2 rounded-full bg-cyanGlow animate-ping" />
        <span className="font-mono text-cyanGlow">JARVIS HUD</span>
        <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] text-slate-400 font-mono">Alt + Space</span>
      </button>

      {/* Spotlight HUD Modal */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/80 p-4 backdrop-blur-md"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl overflow-hidden rounded-2xl border border-cyanGlow/40 bg-gradient-to-b from-slate-950/95 via-[#070b18]/95 to-slate-950/95 p-4 shadow-2xl backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-150"
          >
            {/* Input Bar */}
            <form onSubmit={handleSearch} className="flex items-center gap-3 border-b border-white/10 pb-3">
              <Sparkles className="text-cyanGlow shrink-0" size={20} />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask Jarvis anything from your captured memory vault..."
                className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500 font-medium"
              />
              {isSearching ? (
                <Cpu className="text-cyanGlow animate-spin shrink-0" size={18} />
              ) : (
                <button type="submit" className="flex items-center gap-1 rounded bg-white/10 px-2 py-1 text-[10px] font-mono text-slate-300">
                  <CornerDownLeft size={11} /> Enter
                </button>
              )}
            </form>

            {/* Response Section */}
            {response && (
              <div className="mt-3.5 max-h-56 overflow-y-auto rounded-xl border border-white/10 bg-black/40 p-3.5 text-xs leading-relaxed text-slate-200">
                <p className="font-semibold text-cyanGlow mb-1">Jarvis Response:</p>
                <p className="whitespace-pre-wrap">{response}</p>
              </div>
            )}

            {/* Proactive Connection Banner if Active */}
            {proactiveAlert && (
              <div className="mt-3 rounded-xl border border-amber-400/30 bg-amber-500/10 p-3 text-xs text-amber-200">
                <div className="flex items-center gap-2 font-bold mb-1">
                  <Zap size={14} className="text-amber-400" />
                  <span>{proactiveAlert.title}</span>
                </div>
                <p className="text-[11px] text-amber-300/80 leading-relaxed">{proactiveAlert.connection}</p>
              </div>
            )}

            {/* Quick Action Navigation Buttons */}
            <div className="mt-3.5 flex flex-wrap items-center justify-between gap-2 border-t border-white/5 pt-2 text-[11px] text-slate-400">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => { setIsOpen(false); navigate('/graph'); }}
                  className="flex items-center gap-1 transition hover:text-cyanGlow"
                >
                  <span>Knowledge Graph</span> &rarr;
                </button>
                <button
                  type="button"
                  onClick={() => { setIsOpen(false); navigate('/voice-assistant'); }}
                  className="flex items-center gap-1 transition hover:text-mintGlow"
                >
                  <span>Voice Companion</span> &rarr;
                </button>
              </div>

              <span className="text-[10px] text-slate-500 font-mono">Press Esc to close</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
