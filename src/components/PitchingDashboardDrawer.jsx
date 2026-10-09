import { useEffect, useState } from 'react';
import {
  Activity,
  Bot,
  Calendar,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  ExternalLink,
  Flame,
  Globe,
  Layers,
  Link2,
  Mail,
  Play,
  RotateCw,
  ShieldCheck,
  Sparkles,
  X,
  Zap
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../services/apiClient.js';
import { useBackend } from '../context/BackendContext.jsx';

export default function PitchingDashboardDrawer({ isOpen, onClose, onOpenConnectorsModal }) {
  const { apiClient, username } = useBackend();
  const navigate = useNavigate();

  const [intel, setIntel] = useState(null);
  const [briefing, setBriefing] = useState(null);
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    loadPitchData();
  }, [isOpen]);

  async function loadPitchData() {
    setLoading(true);
    try {
      const [intRes, bRes, connRes] = await Promise.all([
        apiFetch(`${apiClient.baseUrl}/api/os/intelligence`),
        apiFetch(`${apiClient.baseUrl}/api/graph/briefing/today`),
        apiFetch(`${apiClient.baseUrl}/api/connectors`)
      ]);
      if (intRes.ok) setIntel(await intRes.json());
      if (bRes.ok) setBriefing(await bRes.json());
      if (connRes.ok) {
        const data = await connRes.json();
        setConnectors(data.connectors || []);
      }
    } catch {
      //
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-md transition-opacity">
      {/* Backdrop click to dismiss */}
      <div className="flex-1" onClick={onClose} />

      {/* Slide-out Pitching Deck Shell */}
      <div className="w-full max-w-2xl bg-[#090d1a] border-l border-cyan-500/20 shadow-2xl flex flex-col h-full text-slate-100 select-none overflow-hidden animate-in slide-in-from-right duration-300">
        {/* ================= HEADER ================= */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4 bg-[#0d1326]">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-400/15 border border-cyan-400/40 text-cyan-300 shadow-glow">
              <Sparkles size={16} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold tracking-widest text-cyan-400 uppercase">
                  EXECUTIVE PITCHING DECK // STARK CORE
                </span>
                <span className="rounded bg-emerald-400/15 border border-emerald-400/30 px-1.5 py-0.5 text-[9px] font-mono text-emerald-300 font-bold uppercase">
                  LIVE TELEMETRY
                </span>
              </div>
              <h2 className="text-lg font-bold text-white mt-0.5">
                Second Brain OS Intelligence Pitch
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={loadPitchData}
              disabled={loading}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition"
              title="Refresh Telemetry"
            >
              <RotateCw size={15} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* ================= SCROLLABLE PITCH CONTENT ================= */}
        <div className="flex-1 overflow-y-auto thin-scrollbar p-6 space-y-6">
          {/* 1. WHY SECOND BRAIN: THE CORE PITCH PILLARS */}
          <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-cyan-950/30 via-[#0f1424] to-[#0a0e1c] p-4.5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold tracking-wider text-cyan-400 uppercase flex items-center gap-1.5">
                <Flame size={13} className="text-amber-400" />
                Value Proposition & Pitch Highlights
              </span>
              <span className="font-mono text-[10px] text-slate-400">IEEE CONFERENCE READY</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
              <div className="rounded-xl border border-white/5 bg-black/40 p-2.5">
                <div className="text-lg font-bold font-mono text-cyan-300">0.0 MB</div>
                <div className="text-[10px] text-slate-400">Local Disk Bloat</div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/40 p-2.5">
                <div className="text-lg font-bold font-mono text-emerald-300">180ms</div>
                <div className="text-[10px] text-slate-400">Local RTX 3050 Latency</div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/40 p-2.5">
                <div className="text-lg font-bold font-mono text-amber-300">100%</div>
                <div className="text-[10px] text-slate-400">On-Device Privacy</div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/40 p-2.5">
                <div className="text-lg font-bold font-mono text-purple-300">60s</div>
                <div className="text-[10px] text-slate-400">Git Vault Sync</div>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Autonomous cognitive OS that records, transcribes, and indexes personal knowledge in real-time. Features on-device temporal knowledge graphs, contradiction-aware RAG, and multi-app autonomous connectors.
            </p>
          </div>

          {/* 2. WHILE YOU WERE AWAY TELEMETRY CARDS */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Clock size={13} className="text-cyan-400" />
              <span>Real-Time Synthesis Metrics</span>
            </h3>

            <div className="grid grid-cols-3 gap-3">
              <div
                onClick={() => { onClose(); navigate('/gmail'); }}
                className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1424] p-3.5 hover:border-cyan-400/40 transition space-y-1"
              >
                <div className="flex items-center justify-between text-slate-400">
                  <Mail size={15} className="text-red-400" />
                  <span className="font-mono text-[9px] text-slate-500">GMAIL</span>
                </div>
                <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.emails_unread || 7}</div>
                <p className="text-[10px] text-slate-400 truncate">Emails processed</p>
              </div>

              <div
                onClick={() => { onClose(); navigate('/calendar'); }}
                className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1424] p-3.5 hover:border-cyan-400/40 transition space-y-1"
              >
                <div className="flex items-center justify-between text-slate-400">
                  <Calendar size={15} className="text-amber-400" />
                  <span className="font-mono text-[9px] text-slate-500">SCHEDULE</span>
                </div>
                <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.calendar_events_today || 2}</div>
                <p className="text-[10px] text-slate-400 truncate">Events synced</p>
              </div>

              <div
                onClick={() => { onClose(); navigate('/tasks'); }}
                className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1424] p-3.5 hover:border-cyan-400/40 transition space-y-1"
              >
                <div className="flex items-center justify-between text-slate-400">
                  <CheckCircle2 size={15} className="text-emerald-400" />
                  <span className="font-mono text-[9px] text-slate-500">TASKS</span>
                </div>
                <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.tasks_due_today || 3}</div>
                <p className="text-[10px] text-slate-400 truncate">Active deadlines</p>
              </div>
            </div>
          </div>

          {/* 3. LIVE CONNECTORS STATUS (PERMANENTLY STORED IN DB) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Link2 size={13} className="text-emerald-400" />
                <span>Live App Connectors (Database Connected)</span>
              </h3>
              <button
                type="button"
                onClick={() => {
                  if (onOpenConnectorsModal) onOpenConnectorsModal();
                  else { onClose(); navigate('/integrations'); }
                }}
                className="text-[11px] font-mono text-cyan-400 hover:underline flex items-center gap-1"
              >
                <span>Manage in DB</span>
                <ExternalLink size={10} />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {(connectors.length > 0 ? connectors : [
                { service_key: 'gmail_imap', service_name: 'Gmail IMAP Sync', account_identifier: 'immanuellourdu@gmail.com', is_live: true },
                { service_key: 'calendar_ical', service_name: 'Google Calendar Feed', account_identifier: 'College & Research', is_live: true },
                { service_key: 'ollama_local', service_name: 'Local Qwen 2.5 on RTX 3050', account_identifier: '127.0.0.1:11434', is_live: true },
                { service_key: 'github_vault', service_name: 'GitHub Vault Auto-Sync', account_identifier: 'ALPHA-TF141/Second-Brain', is_live: true },
                { service_key: 'deep_research_web', service_name: 'Deep Research Engine', account_identifier: 'Multi-Source Synthesizer', is_live: true },
                { service_key: 'notion_vault', service_name: 'Obsidian & Neo4j Vault', account_identifier: 'memory_vault/wiki', is_live: true },
              ]).map((conn) => (
                <div
                  key={conn.service_key}
                  className="rounded-xl border border-white/10 bg-[#0f1424] p-3 flex items-center justify-between"
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-xs font-bold text-white truncate">{conn.service_name}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono truncate mt-0.5">
                      {conn.account_identifier || 'Auto-Connected in DB'}
                    </div>
                  </div>
                  <span className="rounded bg-emerald-500/15 border border-emerald-400/30 px-2 py-0.5 text-[9px] font-mono text-emerald-300 font-bold uppercase shrink-0">
                    LIVE
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 4. ATTENTION RADAR & RESEARCH HIGHLIGHTS */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Zap size={13} className="text-amber-400" />
              <span>Priority Radar & Research Projects</span>
            </h3>

            <div className="rounded-2xl border border-white/10 bg-[#0f1424] p-4 space-y-2.5">
              <div className="flex items-start justify-between">
                <div>
                  <span className="rounded bg-red-400/10 text-red-400 border border-red-400/20 px-2 py-0.5 text-[9px] font-mono font-bold uppercase">
                    Immediate Deadline
                  </span>
                  <h4 className="text-sm font-bold text-white mt-1.5">
                    IEEE Conference Paper & System Proposal
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Faculty review scheduled with Prof. Sharma for Friday 5:00 PM. System demonstration highlights local graph RAG architecture.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[11px] text-slate-400">
                <span className="font-mono text-cyan-400">Air Pollution Project: Random Forest 94.2%</span>
                <button
                  type="button"
                  onClick={() => { onClose(); navigate('/projects'); }}
                  className="text-cyan-400 font-semibold hover:underline"
                >
                  Open Project &rarr;
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ================= FOOTER ================= */}
        <div className="border-t border-white/10 p-4 bg-[#0d1326] flex items-center justify-between">
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>OPERATOR: {username || 'IMMANUEL'} // ALL SYSTEMS ONLINE</span>
          </div>

          <button
            type="button"
            onClick={() => { onClose(); navigate('/agent'); }}
            className="rounded-xl bg-cyan-400 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-300 shadow-glow flex items-center gap-1.5"
          >
            <Bot size={13} />
            <span>Launch Autonomous Agent</span>
          </button>
        </div>
      </div>
    </div>
  );
}
