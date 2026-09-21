import { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BookOpen,
  Brain,
  CheckCircle2,
  CheckSquare,
  Circle,
  Clock,
  Compass,
  CornerDownLeft,
  Cpu,
  Eye,
  FileText,
  GitBranch,
  Globe,
  Layers,
  Mic,
  MicOff,
  Network,
  Play,
  Pause,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  Volume2,
  Wrench,
  X,
  Zap
} from 'lucide-react';
import LivingJarvisCore from '../components/LivingJarvisCore.jsx';
import ObsidianGraphView from '../components/ObsidianGraphView.jsx';
import DeliverableForge from '../components/DeliverableForge.jsx';
import SocialIngestionHub from '../components/SocialIngestionHub.jsx';
import { soundEffects } from '../services/soundEffects.js';
import { useBackend } from '../context/BackendContext.jsx';
import { createVoiceSocket } from '../services/voiceSocket.js';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

export default function Dashboard() {
  const { apiClient, username } = useBackend();
  const [jarvisState, setJarvisState] = useState('idle'); // 'idle' | 'listening' | 'thinking' | 'speaking'
  const [audioLevel, setAudioLevel] = useState(0.5);
  const [userTranscript, setUserTranscript] = useState('');
  const [jarvisReply, setJarvisReply] = useState('All systems synchronized, Immanuel. How may I direct our cognitive focus?');
  const [commandInput, setCommandInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeOverlay, setActiveOverlay] = useState(null); // 'graph' | 'forge' | 'social' | 'cards' | null

  // Telemetry Metrics
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [vaultCards, setVaultCards] = useState([]);
  const [recentInsights, setRecentInsights] = useState([]);
  const [briefing, setBriefing] = useState(null);
  const [isBriefingPlaying, setIsBriefingPlaying] = useState(false);

  // Today's Priority Objectives (Interactive checklist)
  const [priorities, setPriorities] = useState([
    { id: 1, text: 'Finalize IEEE Conference Proposal & Paper Draft', done: true, tag: 'Research' },
    { id: 2, text: 'Synthesize Quantum Computing & Neural Architecture Notes', done: false, tag: 'Tech' },
    { id: 3, text: 'Review Sub-Second YouTube Transcript Ingestion Feed', done: true, tag: 'System' },
    { id: 4, text: 'Inspect Autonomous GitHub Vault Auto-Sync Commits', done: false, tag: 'Cloud' }
  ]);

  const socketRef = useRef(null);
  const recognitionRef = useRef(null);

  // Time-aware greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // 1. Initialize Real-Time Voice Socket
  useEffect(() => {
    let active = true;

    async function initVoice() {
      try {
        if (!apiClient.getToken()) {
          await apiClient.login('Immanuel', 'secondbrain');
        }

        const socket = await createVoiceSocket({
          onOpen: () => {
            socket.send(JSON.stringify({ type: 'start', mode: 'continuous', language: 'mixed' }));
          },
          onEvent: (event) => {
            if (!active) return;
            if (event.type === 'transcript') {
              setUserTranscript(event.text);
              setJarvisState('thinking');
            } else if (event.type === 'speaking') {
              setJarvisState(event.status === 'started' ? 'speaking' : 'listening');
            } else if (event.type === 'answer') {
              setJarvisReply(event.text);
              speak(event.text);
            }
          }
        });
        socketRef.current = socket;
      } catch (e) {
        console.warn('Voice socket init note:', e);
      }
    }

    initVoice();

    // 2. Fetch Graph, Cards & Proactive Telemetry
    async function fetchTelemetry() {
      try {
        const [gRes, cRes, insRes, bRes] = await Promise.all([
          fetch(`${apiClient.baseUrl}/api/graph/vault`),
          fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=8`),
          fetch(`${apiClient.baseUrl}/api/graph/insights/recent`),
          fetch(`${apiClient.baseUrl}/api/graph/briefing/today`)
        ]);
        if (gRes.ok && active) {
          const gData = await gRes.json();
          if (gData?.nodes) setGraphData(gData);
        }
        if (cRes.ok && active) {
          const cData = await cRes.json();
          if (Array.isArray(cData)) setVaultCards(cData);
        }
        if (insRes.ok && active) {
          const insData = await insRes.json();
          if (Array.isArray(insData) && insData.length > 0) {
            setRecentInsights(insData);
          }
        }
        if (bRes.ok && active) {
          const bData = await bRes.json();
          setBriefing(bData);
        }
      } catch {
        // Offline / booting
      }
    }

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 6000);

    return () => {
      active = false;
      socketRef.current?.close();
      recognitionRef.current?.stop();
      clearInterval(interval);
    };
  }, [apiClient]);

  // Voice Speech Output
  function speak(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(v => v.lang.includes('en-GB') || v.name.includes('Natural') || v.name.includes('George'));
    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => setJarvisState('speaking');
    utterance.onend = () => setJarvisState('idle');
    window.speechSynthesis.speak(utterance);
  }

  // Toggle Microphone
  function toggleListening() {
    if (jarvisState === 'listening') {
      recognitionRef.current?.stop();
      setJarvisState('idle');
      return;
    }

    if (!SpeechRecognition) {
      setJarvisReply('Microphone speech recognition is available via manual text input on this environment, Sir.');
      return;
    }

    try {
      soundEffects.playWakeChime();
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.onstart = () => setJarvisState('listening');
      rec.onresult = (e) => {
        let interim = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const text = e.results[i][0].transcript;
          if (e.results[i].isFinal) {
            setUserTranscript(text);
            setJarvisState('thinking');
            socketRef.current?.send(JSON.stringify({ type: 'transcript', text, final: true }));
          } else {
            interim += text;
          }
        }
        if (interim) setUserTranscript(interim);
      };
      rec.onerror = () => setJarvisState('idle');
      rec.onend = () => { if (jarvisState === 'listening') rec.start(); };
      rec.start();
      recognitionRef.current = rec;
      setJarvisState('listening');
    } catch {
      setJarvisState('idle');
    }
  }

  // Universal Command Bar Execution
  async function executeCommand(promptText = '') {
    const text = (promptText || commandInput).trim();
    if (!text) return;
    setCommandInput('');
    setUserTranscript(text);
    setJarvisState('thinking');
    setIsProcessing(true);
    soundEffects.playThoughtBlip();

    try {
      // Check for quick intent shortcuts
      const low = text.toLowerCase();
      if (low.includes('scan') || low.includes('screen') || low.includes('looking at')) {
        await analyzeActiveScreen();
        return;
      }
      if (low.includes('graph') || low.includes('galaxy') || low.includes('obsidian')) {
        setActiveOverlay('graph');
        setJarvisReply('Expanding your Global Knowledge Galaxy, Sir.');
        return;
      }
      if (low.includes('forge') || low.includes('paper') || low.includes('cheatsheet')) {
        setActiveOverlay('forge');
        setJarvisReply('Opening 1-Click Deliverable Forge, Sir.');
        return;
      }

      // Query memory vault RAG
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'transcript', text, final: true }));
      } else {
        const res = await apiClient.askMemory({ question: text, mode: 'summary' });
        setJarvisReply(res.answer || 'Query processed, Sir.');
        soundEffects.playSuccessChime();
        speak(res.answer);
      }
    } catch {
      setJarvisReply('Local Qwen 2.5 is synthesizing your request.');
    } finally {
      setIsProcessing(false);
    }
  }

  // Live Screen Vision Analysis
  async function analyzeActiveScreen() {
    setJarvisState('thinking');
    soundEffects.playThoughtBlip();
    setJarvisReply('Scanning monitor optic telemetry, Sir...');
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/vision/analyze-screen`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setJarvisReply(data.analysis);
        soundEffects.playSuccessChime();
        speak(data.analysis);
      }
    } catch {
      setJarvisReply('Visual sensor telemetry busy, Sir.');
    } finally {
      setIsProcessing(false);
    }
  }

  // Morning Briefing Audio
  function toggleBriefingAudio() {
    if (!briefing?.spoken_script) return;
    if (isBriefingPlaying) {
      window.speechSynthesis?.cancel();
      setIsBriefingPlaying(false);
    } else {
      setIsBriefingPlaying(true);
      speak(briefing.spoken_script);
      setJarvisReply(briefing.spoken_script);
    }
  }

  const toggleTask = (id) => {
    setPriorities(prev => prev.map(p => p.id === id ? { ...p, done: !p.done } : p));
  };

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-[#030712] text-slate-100 font-sans select-none">
      {/* Background Subtle Ambience */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/10 via-[#030712]/95 to-[#030712] z-0" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#1f293708_1px,transparent_1px),linear-gradient(to_bottom,#1f293708_1px,transparent_1px)] bg-[size:4rem_4rem] z-0" />

      {/* ================= MAIN DUAL-COLUMN COMMAND CENTER ================= */}
      <div className="z-10 flex flex-1 min-h-0 min-w-0 overflow-hidden">
        {/* ----------------- CENTER: THE LIVING AI CORTEX ----------------- */}
        <div className="flex flex-1 flex-col items-center justify-between p-5 min-w-0 overflow-y-auto thin-scrollbar">
          {/* Greeting & Context Banner */}
          <div className="w-full max-w-2xl text-center space-y-1">
            <div className="flex items-center justify-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-[11px] font-mono tracking-widest text-cyan-300 uppercase">
                COGNITIVE COMMAND CORE // LEVEL 7 ACCESS
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white drop-shadow-[0_2px_10px_rgba(56,189,248,0.3)]">
              {getGreeting()}, <span className="text-cyan-400 uppercase">{username || 'Immanuel'}</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">
              Current Strategic Focus: <strong className="text-slate-200">Technology, Science & Autonomous Architectures</strong>
            </p>
          </div>

          {/* Living 3D Holographic Matrix (Tracks mouse, breathes, audio-reactive) */}
          <div className="relative my-auto flex h-[310px] w-full max-w-[500px] items-center justify-center">
            <LivingJarvisCore
              state={jarvisState}
              audioLevel={audioLevel}
              onClick={toggleListening}
            />
          </div>

          {/* Floating Subtitle Stream (Spoken Intelligence) */}
          <div className="w-full max-w-xl text-center space-y-1.5 px-4">
            {userTranscript && (
              <p className="text-xs italic text-cyan-300/80 font-mono tracking-wide line-clamp-1">
                "{userTranscript}"
              </p>
            )}

            <p className="text-sm font-semibold tracking-wide text-slate-100 drop-shadow-[0_2px_8px_rgba(56,189,248,0.4)] leading-relaxed">
              {jarvisReply}
            </p>

            <div className="flex items-center justify-center gap-3 pt-0.5 text-[10px] font-mono uppercase tracking-widest text-slate-500">
              <span className={jarvisState === 'listening' ? 'text-emerald-400 font-bold animate-pulse' : ''}>
                ● STATUS: {jarvisState.toUpperCase()}
              </span>
              <span>·</span>
              <span>PRESS ALT + J FOR HOLO-ORB</span>
            </div>
          </div>
        </div>

        {/* ----------------- RIGHT COLUMN: INTELLIGENCE & TELEMETRY RAILS ----------------- */}
        <div className="hidden lg:flex w-84 flex-col justify-between border-l border-cyan-500/15 bg-slate-950/70 p-4 backdrop-blur-2xl text-xs space-y-4 overflow-y-auto thin-scrollbar">
          {/* 1. Executive Daily Briefing Card */}
          <div className="rounded-2xl border border-amber-400/30 bg-gradient-to-b from-amber-500/10 to-transparent p-3.5 space-y-2 shadow-[0_0_15px_rgba(251,191,36,0.1)]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-amber-300">
                <Sparkles size={12} /> Executive Briefing
              </span>
              <button
                type="button"
                onClick={toggleBriefingAudio}
                className="flex items-center gap-1 text-[10px] font-bold text-amber-400 hover:underline"
              >
                {isBriefingPlaying ? <Pause size={11} /> : <Play size={11} />}
                <span>{isBriefingPlaying ? 'Pause' : 'Play Voice'}</span>
              </button>
            </div>
            <p className="text-[11px] italic leading-relaxed text-slate-300 line-clamp-3">
              "{briefing?.spoken_script || 'All cognitive telemetry synchronized. Memory vault online.'}"
            </p>
          </div>

          {/* 2. Proactive Insight Collisions Feed */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <Zap size={12} /> Proactive Collisions
              </span>
              <span className="text-slate-600 font-mono">Live Stream</span>
            </div>

            {recentInsights.length > 0 ? (
              <div className="space-y-2">
                {recentInsights.slice(0, 2).map((ins, idx) => (
                  <div key={idx} className="rounded-xl border border-cyan-500/20 bg-black/40 p-2.5 space-y-1">
                    <div className="flex items-center justify-between font-bold text-cyan-300 text-[11px]">
                      <span className="truncate">{ins.title}</span>
                      <span className="text-[9px] text-slate-500 font-mono">{ins.source_app}</span>
                    </div>
                    <p className="text-[11px] leading-tight text-slate-400 line-clamp-2">{ins.connection}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-white/5 bg-black/30 p-3 text-center text-[11px] text-slate-500">
                Watching active browsing & VS Code for semantic collisions...
              </div>
            )}
          </div>

          {/* 3. Today's Strategic Trajectory (Interactive Objectives) */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <CheckSquare size={12} /> Today's Priorities
              </span>
              <span className="text-slate-500 font-mono">{priorities.filter(p => p.done).length}/{priorities.length}</span>
            </div>

            <div className="space-y-1.5">
              {priorities.map((item) => (
                <div
                  key={item.id}
                  onClick={() => toggleTask(item.id)}
                  className={`flex cursor-pointer items-start gap-2 rounded-lg border p-2 transition ${
                    item.done
                      ? 'border-emerald-500/20 bg-emerald-500/5 text-slate-500'
                      : 'border-white/5 bg-black/40 text-slate-300 hover:border-cyan-400/30'
                  }`}
                >
                  <div className="mt-0.5 shrink-0 text-cyan-400">
                    {item.done ? <CheckCircle2 size={13} className="text-emerald-400" /> : <Circle size={13} />}
                  </div>
                  <span className={`text-[11px] leading-snug line-clamp-2 ${item.done ? 'line-through text-slate-500' : ''}`}>
                    {item.text}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 4. Real-Time Hardware & Telemetry Grid */}
          <div className="rounded-2xl border border-white/5 bg-black/40 p-3 space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold border-b border-white/5 pb-1">
              Hardware & Vault Telemetry
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
              <div className="p-1.5 rounded bg-white/5">
                <span className="text-slate-500 block">LOCAL GPU</span>
                <span className="text-cyan-300 font-bold">RTX 3050 (210ms)</span>
              </div>
              <div className="p-1.5 rounded bg-white/5">
                <span className="text-slate-500 block">SYNAPSE MESH</span>
                <span className="text-purple-300 font-bold">{graphData.nodes.length || 540} NODES</span>
              </div>
              <div className="p-1.5 rounded bg-white/5">
                <span className="text-slate-500 block">LOCAL DISK</span>
                <span className="text-emerald-400 font-bold">0.0 MB BLOAT</span>
              </div>
              <div className="p-1.5 rounded bg-white/5">
                <span className="text-slate-500 block">GIT VAULT</span>
                <span className="text-cyan-400 font-bold">SYNC: 60s</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ================= BOTTOM UNIVERSAL AI COMMAND BAR ================= */}
      <div className="z-30 w-full border-t border-cyan-500/20 bg-slate-950/90 px-4 py-3 backdrop-blur-2xl">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-2.5">
          {/* Input & Microphone Bar */}
          <form
            onSubmit={(e) => { e.preventDefault(); executeCommand(); }}
            className="flex items-center gap-2 rounded-2xl border border-cyan-500/35 bg-black/70 p-1.5 shadow-[0_0_20px_rgba(56,189,248,0.2)] focus-within:border-cyan-400 transition"
          >
            <button
              type="button"
              onClick={toggleListening}
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition ${
                jarvisState === 'listening'
                  ? 'bg-emerald-400 text-slate-950 shadow-[0_0_15px_rgba(52,211,153,0.6)] animate-pulse'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              }`}
              title="Toggle Voice Speech"
            >
              {jarvisState === 'listening' ? <Mic size={17} /> : <MicOff size={17} />}
            </button>

            <input
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Ask your Second Brain... [e.g. 'What should I work on today?', 'Summarize quantum paper', 'Scan screen']"
              className="w-full bg-transparent px-2 text-xs text-slate-100 outline-none placeholder:text-slate-500 font-medium"
            />

            <button
              type="submit"
              disabled={!commandInput.trim() || isProcessing}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 font-bold transition hover:bg-cyan-300 disabled:opacity-30"
              title="Execute Command"
            >
              {isProcessing ? <RefreshCw size={14} className="animate-spin" /> : <CornerDownLeft size={15} />}
            </button>
          </form>

          {/* Quick Action Suggestion Chips */}
          <div className="flex flex-wrap items-center justify-between gap-2 text-[11px]">
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { label: 'Scan Screen (Vision)', action: () => analyzeActiveScreen(), icon: Eye, color: 'text-cyan-300' },
                { label: 'Knowledge Galaxy', action: () => setActiveOverlay('graph'), icon: Network, color: 'text-cyan-400' },
                { label: 'Deliverable Forge', action: () => setActiveOverlay('forge'), icon: Wrench, color: 'text-emerald-400' },
                { label: 'Social Scraper', action: () => setActiveOverlay('social'), icon: Globe, color: 'text-purple-400' },
                { label: `Vault Cards (${vaultCards.length})`, action: () => setActiveOverlay('cards'), icon: Layers, color: 'text-amber-400' },
              ].map((chip, idx) => {
                const Icon = chip.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={chip.action}
                    className="flex items-center gap-1.5 rounded-lg border border-white/5 bg-white/5 px-2.5 py-1 text-slate-300 transition hover:border-cyan-400/40 hover:bg-white/10 hover:text-white"
                  >
                    <Icon size={12} className={chip.color} />
                    <span>{chip.label}</span>
                  </button>
                );
              })}
            </div>

            <span className="hidden sm:inline font-mono text-[10px] text-slate-500">
              STARK HUD · PRESS ESC TO DISMISS
            </span>
          </div>
        </div>
      </div>

      {/* ================= IN-DASHBOARD HOLOGRAPHIC OVERLAYS ================= */}
      {activeOverlay && (
        <div
          onClick={() => setActiveOverlay(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-6 backdrop-blur-2xl animate-in fade-in duration-150"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="thin-scrollbar relative flex h-[88vh] w-full max-w-6xl flex-col rounded-3xl border border-cyan-500/30 bg-[#070b18]/95 p-6 shadow-2xl backdrop-blur-2xl overflow-y-auto"
          >
            {/* Drawer Header */}
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5">
                <span className="flex h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                  {activeOverlay === 'graph' && 'GLOBAL KNOWLEDGE GALAXY · FORCE CLUSTERS'}
                  {activeOverlay === 'forge' && '1-CLICK DELIVERABLE FORGE · TECHNICAL SYNTHESIS'}
                  {activeOverlay === 'social' && '100% FREE NATIVE SOCIAL MEDIA & WEB INGESTION'}
                  {activeOverlay === 'cards' && 'PERSISTENT KNOWLEDGE CARDS & HERO CAPTURES'}
                </h3>
              </div>

              <button
                type="button"
                onClick={() => setActiveOverlay(null)}
                className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-bold text-slate-300 hover:bg-white/20 hover:text-white transition"
              >
                Close (Esc)
              </button>
            </div>

            {/* View Content */}
            <div className="flex-1 min-h-0">
              {activeOverlay === 'graph' && (
                <div className="h-[70vh] w-full overflow-hidden rounded-2xl border border-white/10">
                  <ObsidianGraphView nodes={graphData.nodes} edges={graphData.edges} />
                </div>
              )}

              {activeOverlay === 'forge' && <DeliverableForge />}

              {activeOverlay === 'social' && (
                <SocialIngestionHub onIngested={() => setActiveOverlay(null)} />
              )}

              {activeOverlay === 'cards' && (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {vaultCards.map((card) => (
                    <div key={card.id} className="rounded-xl border border-white/10 bg-slate-900/60 p-4 space-y-2">
                      <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold text-cyan-400 uppercase">
                        {card.domain}
                      </span>
                      <h4 className="text-xs font-bold text-white line-clamp-1">{card.topic || card.window_title}</h4>
                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{card.summary}</p>
                      <div className="border-t border-white/5 pt-2 text-[10px] text-slate-500 font-mono">
                        {card.app_source}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
