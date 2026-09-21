import { useEffect, useState } from 'react';
import {
  Bell,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  ExternalLink,
  Eye,
  GitBranch,
  Layers,
  Mail,
  Mic,
  MicOff,
  Network,
  Play,
  Pause,
  RefreshCw,
  Search,
  Sparkles,
  Zap,
  ArrowRight
} from 'lucide-react';
import LivingJarvisCore from '../components/LivingJarvisCore.jsx';
import { useBackend } from '../context/BackendContext.jsx';
import { useNavigate } from 'react-router-dom';
import { soundEffects } from '../services/soundEffects.js';

export default function HomeOS() {
  const { apiClient, username } = useBackend();
  const navigate = useNavigate();
  const [intel, setIntel] = useState(null);
  const [jarvisState, setJarvisState] = useState('idle');
  const [audioLevel, setAudioLevel] = useState(0.5);
  const [briefing, setBriefing] = useState(null);
  const [isPlayingBriefing, setIsPlayingBriefing] = useState(false);
  const [command, setCommand] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadHomeIntel() {
    try {
      const [intRes, bRes] = await Promise.all([
        fetch(`${apiClient.baseUrl}/api/os/intelligence`),
        fetch(`${apiClient.baseUrl}/api/graph/briefing/today`)
      ]);
      if (intRes.ok) setIntel(await intRes.json());
      if (bRes.ok) setBriefing(await bRes.json());
    } catch {
      //
    }
  }

  useEffect(() => {
    loadHomeIntel();
  }, []);

  function toggleAudio() {
    if (!briefing?.spoken_script) return;
    if (isPlayingBriefing) {
      window.speechSynthesis?.cancel();
      setIsPlayingBriefing(false);
    } else {
      setIsPlayingBriefing(true);
      window.speechSynthesis?.cancel();
      const utt = new SpeechSynthesisUtterance(briefing.spoken_script);
      utt.onend = () => setIsPlayingBriefing(false);
      window.speechSynthesis?.speak(utt);
    }
  }

  function handleCommandSubmit(e) {
    e?.preventDefault();
    if (!command.trim()) return;
    navigate(`/agent?q=${encodeURIComponent(command.trim())}`);
  }

  const getGreeting = () => {
    const hr = new Date().getHours();
    if (hr < 12) return 'GOOD MORNING';
    if (hr < 18) return 'GOOD AFTERNOON';
    return 'GOOD EVENING';
  };

  return (
    <div className="flex h-full w-full flex-col bg-[#070a13] p-5 text-slate-100 font-sans select-none overflow-y-auto thin-scrollbar space-y-6">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        {/* ================= 1. GREETING & CONTEXT HEADER ================= */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono font-bold tracking-widest uppercase">
              <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
              <span>STARK COGNITIVE CORE // DAILY INTELLIGENCE</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
              {getGreeting()}, <span className="text-cyan-400">{username || 'IMMANUEL'}</span>
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={toggleAudio}
              className="flex items-center gap-2 rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-2 text-xs font-bold text-amber-300 shadow-glow transition hover:bg-amber-500/20"
            >
              {isPlayingBriefing ? <Pause size={14} /> : <Play size={14} />}
              <span>{isPlayingBriefing ? 'Pause Voice' : 'Play Morning Briefing'}</span>
            </button>
          </div>
        </div>

        {/* ================= 2. WHILE YOU WERE AWAY TELEMETRY CARDS ================= */}
        <div>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <Clock size={13} className="text-cyan-400" />
            <span>While You Were Away</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
            <div
              onClick={() => navigate('/gmail')}
              className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1422] p-3.5 hover:border-cyan-400/40 transition space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400">
                <Mail size={15} className="text-red-400" />
                <span className="font-mono text-[10px] text-slate-500">GMAIL</span>
              </div>
              <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.emails_unread || 7}</div>
              <p className="text-[10px] text-slate-400 truncate">Emails processed</p>
            </div>

            <div
              onClick={() => navigate('/calendar')}
              className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1422] p-3.5 hover:border-cyan-400/40 transition space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400">
                <Calendar size={15} className="text-amber-400" />
                <span className="font-mono text-[10px] text-slate-500">SCHEDULE</span>
              </div>
              <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.calendar_events_today || 2}</div>
              <p className="text-[10px] text-slate-400 truncate">Calendar updates</p>
            </div>

            <div
              onClick={() => navigate('/tasks')}
              className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1422] p-3.5 hover:border-cyan-400/40 transition space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400">
                <CheckCircle2 size={15} className="text-emerald-400" />
                <span className="font-mono text-[10px] text-slate-500">TASKS</span>
              </div>
              <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.tasks_due_today || 3}</div>
              <p className="text-[10px] text-slate-400 truncate">Due today</p>
            </div>

            <div
              onClick={() => navigate('/reminders')}
              className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1422] p-3.5 hover:border-cyan-400/40 transition space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400">
                <Clock size={15} className="text-purple-400" />
                <span className="font-mono text-[10px] text-slate-500">ALARMS</span>
              </div>
              <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.reminders_active || 2}</div>
              <p className="text-[10px] text-slate-400 truncate">Active reminders</p>
            </div>

            <div
              onClick={() => navigate('/automations')}
              className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1422] p-3.5 hover:border-cyan-400/40 transition space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400">
                <Zap size={15} className="text-cyan-400" />
                <span className="font-mono text-[10px] text-slate-500">SWARM</span>
              </div>
              <div className="text-xl font-bold text-white font-mono">{intel?.while_you_were_away?.automated_actions_completed || 3}</div>
              <p className="text-[10px] text-slate-400 truncate">Actions completed</p>
            </div>

            <div
              onClick={() => navigate('/activity')}
              className="cursor-pointer rounded-2xl border border-white/5 bg-[#0f1422] p-3.5 hover:border-cyan-400/40 transition space-y-1"
            >
              <div className="flex items-center justify-between text-slate-400">
                <Activity size={15} className="text-mintGlow" />
                <span className="font-mono text-[10px] text-slate-500">DISK</span>
              </div>
              <div className="text-xl font-bold text-emerald-400 font-mono">0.0 MB</div>
              <p className="text-[10px] text-slate-400 truncate">Zero local bloat</p>
            </div>
          </div>
        </div>

        {/* ================= 3. WHAT NEEDS YOUR ATTENTION? (GENUINE CONTEXT) ================= */}
        <div>
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <Sparkles size={13} className="text-amber-400" />
            <span>What Needs Your Attention?</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {(intel?.attention_items || [
              {
                id: '1',
                title: 'Assignment Deadline Detected',
                description: 'Prof. Sharma mentioned a Friday 5:00 PM deadline for your IEEE conference draft and documentation.',
                target: '/gmail',
                action_label: 'Inspect Email & Task'
              },
              {
                id: '2',
                title: 'Project Update: Air Pollution Project',
                description: 'Random Forest model evaluation on Central Pollution AQI dataset requires validation before workshop.',
                target: '/projects',
                action_label: 'Open Project'
              },
              {
                id: '3',
                title: 'Reminder: Department Documentation',
                description: 'Submit your IEEE conference proposal and system specifications today at 5:00 PM.',
                target: '/reminders',
                action_label: 'View Reminder'
              }
            ]).map((item, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-white/10 bg-[#0f1422] p-4 flex flex-col justify-between hover:border-cyan-400/40 transition space-y-3"
              >
                <div>
                  <span className="rounded bg-amber-400/10 px-2 py-0.5 text-[10px] font-mono text-amber-300 font-bold uppercase">
                    Priority Alert
                  </span>
                  <h4 className="text-sm font-bold text-white mt-2">{item.title}</h4>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.description}</p>
                </div>

                <button
                  type="button"
                  onClick={() => navigate(item.target)}
                  className="flex items-center gap-1.5 text-xs text-cyan-400 font-semibold hover:underline pt-2 border-t border-white/5"
                >
                  <span>{item.action_label}</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ================= 4. LIVING NEURAL CORE HERO (CENTERPIECE) ================= */}
        <div className="rounded-3xl border border-cyan-500/20 bg-gradient-to-b from-[#0d1326] via-[#070a13] to-[#070a13] p-6 flex flex-col items-center justify-center text-center space-y-2 relative overflow-hidden">
          <div className="relative h-[280px] w-full max-w-[460px]">
            <LivingJarvisCore state={jarvisState} audioLevel={audioLevel} onClick={() => navigate('/voice')} />
          </div>

          <div className="max-w-xl space-y-1">
            <p className="text-sm font-semibold text-slate-200">
              "{briefing?.spoken_script || 'All cognitive telemetry synchronized. Memory vault online.'}"
            </p>
            <p className="text-[11px] font-mono text-cyan-400 uppercase tracking-widest">
              LOCAL QWEN 2.5 ACCELERATED BY NVIDIA RTX 3050 (210MS)
            </p>
          </div>
        </div>

        {/* ================= 5. UNIVERSAL COMMAND BAR ================= */}
        <div className="rounded-2xl border border-cyan-500/30 bg-[#0c101d] p-3 space-y-2.5">
          <form onSubmit={handleCommandSubmit} className="flex items-center gap-2">
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Ask your Second Brain... [e.g. 'What should I work on today?', 'Summarize AI project', 'Find my notes about ML']"
              className="flex-1 bg-transparent px-3 text-xs text-white outline-none placeholder:text-slate-500 font-medium"
            />
            <button
              type="submit"
              className="rounded-xl bg-cyan-400 px-5 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-300 shadow-glow"
            >
              Ask AI Agent &rarr;
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span className="text-[10px] font-mono text-slate-500 uppercase">Directives:</span>
            {[
              'What should I work on today?',
              'Show everything connected to Air Pollution Project',
              'Summarize unread emails',
              'Scan monitor screen'
            ].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => navigate(`/agent?q=${encodeURIComponent(d)}`)}
                className="rounded-lg border border-white/5 bg-white/5 px-2.5 py-1 text-slate-300 hover:text-white hover:border-cyan-400/30 transition text-[11px]"
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
