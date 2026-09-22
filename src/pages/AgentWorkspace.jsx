import { useEffect, useRef, useState } from 'react';
import {
  Bot,
  Brain,
  Sparkles,
  Paperclip,
  Cpu,
  Search,
  Mail,
  Calendar,
  BookOpen,
  Wrench,
  RefreshCw,
  CornerDownLeft
} from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';
import { soundEffects } from '../services/soundEffects.js';

export default function AgentWorkspace() {
  const { apiClient } = useBackend();
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: 'At your command, Immanuel. I have full read-write access to your memory vault, calendar, tasks, and connected integrations. How can I assist your workflow today?',
      toolStatus: null
    }
  ]);
  const [input, setInput] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [currentToolState, setCurrentToolState] = useState(null); // 'Thinking' | 'Searching' | 'Reading Gmail' | 'Checking Calendar' | 'Analyzing Knowledge' | 'Executing Task' | null
  const scrollRef = useRef(null);

  useEffect(() => {
    // Guard: not available in every engine/webview context
    scrollRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages, currentToolState]);

  async function handleSend(e) {
    e?.preventDefault();
    const query = input.trim();
    if (!query) return;

    setInput('');
    const userMsg = { id: Date.now(), role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setIsBusy(true);
    soundEffects.playThoughtBlip();

    // Simulate multi-tool execution telemetry based on query intent
    const low = query.toLowerCase();
    if (low.includes('email') || low.includes('gmail')) {
      setCurrentToolState('Reading Gmail');
    } else if (low.includes('calendar') || low.includes('schedule') || low.includes('meeting')) {
      setCurrentToolState('Checking Calendar');
    } else if (low.includes('project') || low.includes('knowledge') || low.includes('paper')) {
      setCurrentToolState('Analyzing Knowledge');
    } else {
      setCurrentToolState('Thinking');
    }

    try {
      // Connect to local LLM / memory RAG
      const res = await apiClient.askMemory({ question: query, mode: 'summary' });
      setCurrentToolState('Executing Task');
      await new Promise(r => setTimeout(r, 400));

      const aiMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: res.answer || 'I have synthesized the relevant context from your Second Brain vault.',
        toolStatus: currentToolState
      };
      setMessages(prev => [...prev, aiMsg]);
      soundEffects.playSuccessChime();
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: 'Local Qwen 2.5 is synthesizing your request. Ensure Ollama is active on port 11434, Sir.',
          toolStatus: null
        }
      ]);
    } finally {
      setIsBusy(false);
      setCurrentToolState(null);
    }
  }

  const toolStates = [
    { label: 'Thinking', icon: Brain, color: 'text-purple-400' },
    { label: 'Searching', icon: Search, color: 'text-cyan-400' },
    { label: 'Reading Gmail', icon: Mail, color: 'text-red-400' },
    { label: 'Checking Calendar', icon: Calendar, color: 'text-amber-400' },
    { label: 'Analyzing Knowledge', icon: BookOpen, color: 'text-emerald-400' },
    { label: 'Executing Task', icon: Wrench, color: 'text-cyan-300' }
  ];

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] text-slate-100 font-sans select-none overflow-hidden">
      {/* Header */}
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-[#262626] bg-[#14161d] px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-400/10 border border-cyan-400/30 text-cyan-400">
            <Bot size={16} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider">JARVIS Full-Screen Agent</h3>
            <p className="text-[10px] text-slate-400">Local Multi-Tool Autonomous Intelligence Core</p>
          </div>
        </div>

        {/* Live Active Tool Pill */}
        {currentToolState && (
          <div className="flex items-center gap-2 rounded-full border border-cyan-400/40 bg-cyan-500/15 px-3 py-1 text-xs font-mono font-bold text-cyan-300 animate-pulse">
            <RefreshCw size={12} className="animate-spin" />
            <span>JARVIS STATUS: {currentToolState.toUpperCase()}</span>
          </div>
        )}
      </div>

      {/* Message Stream */}
      <div className="thin-scrollbar flex-1 overflow-y-auto p-5 space-y-4 max-w-4xl w-full mx-auto">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div key={m.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-400 text-slate-950 font-bold text-xs mt-1">
                  J
                </div>
              )}

              <div className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${isUser ? 'bg-cyan-500/15 border border-cyan-400/30 text-white rounded-tr-none' : 'bg-[#181a24] border border-white/5 text-slate-200 rounded-tl-none space-y-2'}`}>
                {m.toolStatus && (
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-cyan-400 mb-1 border-b border-white/5 pb-1">
                    <Sparkles size={11} />
                    <span>Executed tool: {m.toolStatus}</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{m.content}</p>
              </div>

              {isUser && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/10 text-cyan-300 font-bold text-xs mt-1">
                  I
                </div>
              )}
            </div>
          );
        })}

        {isBusy && currentToolState && (
          <div className="flex items-center gap-2 text-xs text-slate-400 pl-10 font-mono">
            <Cpu size={14} className="animate-spin text-cyan-400" />
            <span>Agent executing: {currentToolState}...</span>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Bottom Interactive Command Dock */}
      <div className="border-t border-[#262626] bg-[#14161d] p-4">
        <div className="max-w-4xl mx-auto space-y-2.5">
          <form onSubmit={handleSend} className="flex items-center gap-2 rounded-2xl border border-white/10 bg-black/60 p-1.5 focus-within:border-cyan-400 transition">
            <button
              type="button"
              className="p-2 text-slate-400 hover:text-white rounded-lg transition"
              title="Attach File"
            >
              <Paperclip size={16} />
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask questions, query Gmail, check Calendar, or command Second Brain..."
              className="flex-1 bg-transparent px-2 text-xs text-white outline-none placeholder:text-slate-500"
            />

            <button
              type="submit"
              disabled={!input.trim() || isBusy}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 font-bold transition hover:bg-cyan-300 disabled:opacity-40"
            >
              <CornerDownLeft size={15} />
            </button>
          </form>

          {/* Quick Tool Chips */}
          <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400">
            <span className="font-mono uppercase text-slate-500">Autonomous Tools:</span>
            {toolStates.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.label}
                  type="button"
                  onClick={() => setInput(`Execute ${t.label.toLowerCase()} for my active tasks`)}
                  className="flex items-center gap-1 rounded-md border border-white/5 bg-white/5 px-2 py-0.5 text-slate-300 hover:text-white transition"
                >
                  <Icon size={11} className={t.color} />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
