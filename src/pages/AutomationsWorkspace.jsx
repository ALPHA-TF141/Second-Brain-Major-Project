import { useEffect, useState } from 'react';
import { Bot, Play, Pause, Plus, Sparkles, RefreshCw, Clock, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function AutomationsWorkspace() {
  const { apiClient } = useBackend();
  const [automations, setAutomations] = useState([]);
  const [naturalPrompt, setNaturalPrompt] = useState('');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [runningId, setRunningId] = useState(null);

  async function loadAutomations() {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/automations`);
      if (res.ok) {
        const data = await res.json();
        setAutomations(data);
      }
    } catch {
      //
    }
  }

  useEffect(() => {
    loadAutomations();
  }, []);

  async function toggleStatus(autoId) {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/automations/${autoId}/toggle`, { method: 'POST' });
      if (res.ok) await loadAutomations();
    } catch {
      //
    }
  }

  async function runNow(autoId) {
    setRunningId(autoId);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/os/automations/${autoId}/run`, { method: 'POST' });
      if (res.ok) {
        await loadAutomations();
        alert('✓ Automation workflow executed successfully!');
      }
    } finally {
      setRunningId(null);
    }
  }

  async function createFromPrompt(e) {
    e?.preventDefault();
    if (!naturalPrompt.trim()) return;
    setIsSynthesizing(true);
    try {
      // Create structured automation workflow
      await fetch(`${apiClient.baseUrl}/api/os/automations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: naturalPrompt.slice(0, 36) + '...',
          trigger: 'Scheduled Trigger / Event',
          tools: ['Gmail', 'Tasks', 'Memory Vault'],
          ai_analysis: naturalPrompt,
          action: 'Autonomous AI Synthesis & Push'
        })
      });
      setNaturalPrompt('');
      await loadAutomations();
    } finally {
      setIsSynthesizing(false);
    }
  }

  return (
    <div className="flex h-full w-full flex-col bg-[#111318] p-6 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        <div className="border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Bot size={18} className="text-cyan-400" />
            <h2 className="text-base font-bold text-white uppercase tracking-wider font-mono">Autonomous Automations & Workflows</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Authorizing the Jarvis AI swarm to execute multi-tool scheduled routines.</p>
        </div>

        {/* Natural Language Automation Creator */}
        <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/20 via-[#161820] to-[#161820] p-4.5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-cyan-300">
            <Sparkles size={14} />
            <span>Create Automation via Natural Language</span>
          </div>

          <form onSubmit={createFromPrompt} className="flex gap-2">
            <input
              type="text"
              value={naturalPrompt}
              onChange={(e) => setNaturalPrompt(e.target.value)}
              placeholder="e.g. 'Every morning check my Gmail and tell me what I need to do'..."
              className="flex-1 rounded-xl border border-white/10 bg-black/60 px-3.5 py-2 text-xs text-white outline-none focus:border-cyan-400"
            />
            <button
              type="submit"
              disabled={!naturalPrompt.trim() || isSynthesizing}
              className="flex items-center gap-1.5 rounded-xl bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 shadow-glow disabled:opacity-40"
            >
              {isSynthesizing ? <RefreshCw size={13} className="animate-spin" /> : <Plus size={14} />}
              Synthesize Rule
            </button>
          </form>
        </div>

        {/* Active Automations List */}
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">Active Automations</h3>

          {automations.map((a) => {
            const isActive = a.status === 'active';
            const isRunning = runningId === a.id;

            return (
              <div
                key={a.id}
                className={`rounded-2xl border p-4 transition ${
                  isActive ? 'border-white/10 bg-[#161820]' : 'border-white/5 bg-black/40 opacity-60'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2.5">
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                    <h4 className="text-sm font-bold text-white">{a.name}</h4>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <button
                      type="button"
                      onClick={() => runNow(a.id)}
                      disabled={isRunning}
                      className="flex items-center gap-1 rounded-lg bg-white/10 px-2.5 py-1 text-[11px] font-bold text-cyan-300 hover:bg-white/15 transition"
                    >
                      <Play size={11} className={isRunning ? 'animate-spin' : ''} />
                      {isRunning ? 'Running...' : 'Run Now'}
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleStatus(a.id)}
                      className="rounded-lg border border-white/10 px-2.5 py-1 text-[11px] text-slate-300 hover:bg-white/10 transition"
                    >
                      {isActive ? 'Pause' : 'Enable'}
                    </button>
                  </div>
                </div>

                {/* Workflow Step Breakdown: Trigger -> Tools -> AI Analysis -> Action */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-2 pt-3 text-[11px] font-mono">
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <span className="text-slate-500 block text-[9px] uppercase">1. TRIGGER</span>
                    <span className="text-cyan-300">{a.trigger}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <span className="text-slate-500 block text-[9px] uppercase">2. PERMITTED TOOLS</span>
                    <span className="text-slate-200">{Array.isArray(a.tools) ? a.tools.join(', ') : a.tools}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <span className="text-slate-500 block text-[9px] uppercase">3. AI REASONING</span>
                    <span className="text-amber-300 line-clamp-2">{a.ai_analysis}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <span className="text-slate-500 block text-[9px] uppercase">4. ACTION EXECUTED</span>
                    <span className="text-emerald-300 line-clamp-2">{a.action}</span>
                  </div>
                </div>

                <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span>Last Executed: {a.last_run}</span>
                  <span className="text-cyan-400">Zero Cloud Leak · On-Device</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
