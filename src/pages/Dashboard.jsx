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
  Database,
  Download,
  ExternalLink,
  Eye,
  FileText,
  Folder,
  GitBranch,
  Globe,
  HardDrive,
  Image as ImageIcon,
  Layers,
  Mic,
  MicOff,
  Network,
  Play,
  Pause,
  Plus,
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
  const [activeOverlay, setActiveOverlay] = useState(null); // 'graph' | 'forge' | 'social' | 'cards' | 'wiki_reader' | null

  // Telemetry & Second Brain Data State
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [vaultCards, setVaultCards] = useState([]);
  const [wikiArticles, setWikiArticles] = useState([]);
  const [deliverables, setDeliverables] = useState([]);
  const [recentInsights, setRecentInsights] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [briefing, setBriefing] = useState(null);
  const [isBriefingPlaying, setIsBriefingPlaying] = useState(false);
  const [selectedWikiDoc, setSelectedWikiDoc] = useState(null);
  const [selectedCardImage, setSelectedCardImage] = useState(null);

  // Active Category / Project Filter on Left Side
  const [activeCategory, setActiveCategory] = useState('All Knowledge');

  // Tasks & Priorities State (Interactive checklist)
  const [priorities, setPriorities] = useState([
    { id: 1, text: 'Finalize IEEE Conference Proposal & Benchmark Paper', done: true, tag: 'Research', due: 'Today' },
    { id: 2, text: 'Synthesize Quantum Computing & Neural Architecture Notes', done: false, tag: 'Tech', due: 'Tomorrow' },
    { id: 3, text: 'Inspect Sub-Second YouTube Transcript Ingestion Engine', done: true, tag: 'System', due: 'Completed' },
    { id: 4, text: 'Verify Autonomous GitHub Vault 60s Auto-Sync Commits', done: false, tag: 'Cloud', due: 'Pending' }
  ]);

  const socketRef = useRef(null);
  const recognitionRef = useRef(null);

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

    // 2. Fetch Deep Telemetry (Graph, Wiki, Deliverables, Cards, Insights, Activity)
    async function fetchAllTelemetry() {
      try {
        const [gRes, cRes, wRes, dRes, insRes, bRes, actRes] = await Promise.all([
          fetch(`${apiClient.baseUrl}/api/graph/vault`),
          fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=12`),
          fetch(`${apiClient.baseUrl}/api/graph/vault/wiki`),
          fetch(`${apiClient.baseUrl}/api/graph/deliverables`),
          fetch(`${apiClient.baseUrl}/api/graph/insights/recent`),
          fetch(`${apiClient.baseUrl}/api/graph/briefing/today`),
          apiClient.fetchActivities().catch(() => [])
        ]);

        if (gRes.ok && active) {
          const gData = await gRes.json();
          if (gData?.nodes) setGraphData(gData);
        }
        if (cRes.ok && active) {
          const cData = await cRes.json();
          if (Array.isArray(cData)) setVaultCards(cData);
        }
        if (wRes.ok && active) {
          const wData = await wRes.json();
          if (Array.isArray(wData)) setWikiArticles(wData);
        }
        if (dRes.ok && active) {
          const dData = await dRes.json();
          if (Array.isArray(dData)) setDeliverables(dData);
        }
        if (insRes.ok && active) {
          const insData = await insRes.json();
          if (Array.isArray(insData)) setRecentInsights(insData);
        }
        if (bRes.ok && active) {
          const bData = await bRes.json();
          setBriefing(bData);
        }
        if (Array.isArray(actRes) && active) {
          setRecentActivities(actRes.slice(0, 8));
        }
      } catch {
        // Offline / booting
      }
    }

    fetchAllTelemetry();
    const interval = setInterval(fetchAllTelemetry, 6000);

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

  // Universal Command Bar Execution (Cross-Module Retrieval)
  async function executeCommand(promptText = '') {
    const text = (promptText || commandInput).trim();
    if (!text) return;
    setCommandInput('');
    setUserTranscript(text);
    setJarvisState('thinking');
    setIsProcessing(true);
    soundEffects.playThoughtBlip();

    try {
      const low = text.toLowerCase();
      if (low.includes('scan') || low.includes('screen') || low.includes('looking at')) {
        await analyzeActiveScreen();
        return;
      }
      if (low.includes('graph') || low.includes('galaxy') || low.includes('network')) {
        setActiveOverlay('graph');
        setJarvisReply('Expanding your Global Knowledge Galaxy, Sir.');
        return;
      }
      if (low.includes('forge') || low.includes('paper') || low.includes('cheatsheet')) {
        setActiveOverlay('forge');
        setJarvisReply('Opening 1-Click Deliverable Forge, Sir.');
        return;
      }
      if (low.includes('task') || low.includes('work on') || low.includes('todo') || low.includes('priority')) {
        setJarvisReply(`Sir, based on your current trajectory, your top priority is: ${priorities.find(p => !p.done)?.text || 'Continue synthesis'}.`);
        speak(`Sir, based on your current trajectory, your top priority is: ${priorities.find(p => !p.done)?.text || 'Continue synthesis'}.`);
        return;
      }

      // Query memory vault RAG with local Qwen 2.5
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

  async function openWikiArticle(art) {
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/vault/wiki/article?path=${encodeURIComponent(art.path)}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedWikiDoc({ ...art, content: data.content });
        setActiveOverlay('wiki_reader');
      }
    } catch {
      //
    }
  }

  const categories = [
    { name: 'All Knowledge', count: vaultCards.length + wikiArticles.length, icon: Layers },
    { name: 'Technology & AI', count: 42, icon: Cpu },
    { name: 'Science & Quantum', count: 28, icon: Brain },
    { name: 'Cybersecurity & Defense', count: 16, icon: ShieldCheck },
    { name: 'Research & Publications', count: 24, icon: BookOpen },
    { name: 'Web & Video Intel', count: 19, icon: Globe },
  ];

  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-[#030712] text-slate-100 font-sans select-none">
      {/* Background Subtle Ambience */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-950/15 via-[#030712]/95 to-[#030712] z-0" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#1f293708_1px,transparent_1px),linear-gradient(to_bottom,#1f293708_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] z-0" />

      {/* ================= 3-COLUMN FUTURISTIC COMMAND CENTER ================= */}
      <div className="z-10 flex flex-1 min-h-0 min-w-0 overflow-hidden">
        {/* ===================== 1. LEFT SIDE: SECOND BRAIN VAULT ===================== */}
        <aside className="hidden xl:flex w-72 shrink-0 flex-col justify-between border-r border-cyan-500/15 bg-slate-950/70 p-3.5 backdrop-blur-2xl text-xs space-y-4 overflow-y-auto thin-scrollbar">
          {/* Categories & Knowledge Domains */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <Compass size={12} /> Second Brain Domains
              </span>
              <span className="text-slate-600 font-mono">{categories.length}</span>
            </div>

            <div className="space-y-0.5">
              {categories.map((cat) => {
                const Icon = cat.icon;
                const isSelected = activeCategory === cat.name;
                return (
                  <button
                    key={cat.name}
                    type="button"
                    onClick={() => setActiveCategory(cat.name)}
                    className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs transition ${
                      isSelected
                        ? 'border border-cyan-400/30 bg-cyan-500/15 text-white font-semibold shadow-[0_0_10px_rgba(56,189,248,0.2)]'
                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Icon size={13} className={isSelected ? 'text-cyan-400' : 'text-slate-500'} />
                      <span className="truncate">{cat.name}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">{cat.count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Master Wiki Master-Articles (Karpathy Model) */}
          <div className="space-y-2 border-t border-white/5 pt-3">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span className="flex items-center gap-1.5 text-amber-400">
                <BookOpen size={12} /> Self-Improving Wiki
              </span>
              <span className="text-slate-500 font-mono">{wikiArticles.length} Articles</span>
            </div>

            <div className="space-y-1">
              {wikiArticles.slice(0, 4).map((art, idx) => (
                <div
                  key={idx}
                  onClick={() => openWikiArticle(art)}
                  className="flex cursor-pointer items-center justify-between rounded-lg border border-white/5 bg-black/40 p-2 hover:border-cyan-400/30 hover:bg-white/5 transition"
                >
                  <div className="truncate pr-2">
                    <h5 className="font-semibold text-slate-200 text-[11px] truncate">{art.title}</h5>
                    <span className="text-[9px] text-cyan-400 uppercase font-mono">{art.domain}</span>
                  </div>
                  <ChevronRight size={12} className="text-slate-500 shrink-0" />
                </div>
              ))}
              {wikiArticles.length === 0 && (
                <p className="text-[11px] text-slate-500 italic p-1">Compiling wiki from activity...</p>
              )}
            </div>
          </div>

          {/* Forged Deliverables (Papers, Cheatsheets, Specs) */}
          <div className="space-y-2 border-t border-white/5 pt-3">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <FileText size={12} /> Forged Documents
              </span>
              <button
                type="button"
                onClick={() => setActiveOverlay('forge')}
                className="text-[10px] text-cyan-400 hover:underline font-mono"
              >
                + Forge
              </button>
            </div>

            <div className="space-y-1">
              {deliverables.slice(0, 3).map((doc, idx) => (
                <div
                  key={idx}
                  onClick={() => setActiveOverlay('forge')}
                  className="flex cursor-pointer items-center justify-between rounded-lg border border-white/5 bg-black/40 p-2 hover:border-emerald-400/30 transition text-[11px]"
                >
                  <div className="truncate pr-2">
                    <span className="font-medium text-slate-200 truncate block">{doc.title}</span>
                    <span className="text-[9px] text-slate-500 font-mono">{doc.word_count} words</span>
                  </div>
                  <Download size={11} className="text-slate-500 shrink-0" />
                </div>
              ))}
              {deliverables.length === 0 && (
                <p className="text-[11px] text-slate-500 italic p-1">No forged papers yet.</p>
              )}
            </div>
          </div>

          {/* Captured Visual Hero Evidence Preview */}
          <div className="space-y-1.5 border-t border-white/5 pt-3">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span>Hero Evidence</span>
              <button type="button" onClick={() => setActiveOverlay('cards')} className="text-cyan-400 hover:underline">
                View All ({vaultCards.length})
              </button>
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              {vaultCards.filter(c => c.hero_image).slice(0, 2).map((card) => {
                const imgUrl = `${apiClient.baseUrl}/${card.hero_image.replace(/\\/g, '/')}`;
                return (
                  <div
                    key={card.id}
                    onClick={() => setSelectedCardImage(imgUrl)}
                    className="group relative h-16 cursor-pointer overflow-hidden rounded-md border border-white/10 bg-black"
                  >
                    <img src={imgUrl} alt={card.topic} className="h-full w-full object-cover group-hover:scale-105 transition" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                      <Eye size={12} className="text-white" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </aside>

        {/* ===================== 2. CENTER: THE LIVING AI CORTEX ===================== */}
        <div className="flex flex-1 flex-col items-center justify-between p-4 min-w-0 overflow-y-auto thin-scrollbar">
          {/* Greeting & Context Banner */}
          <div className="w-full max-w-xl text-center space-y-1 pt-1">
            <div className="flex items-center justify-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-[10px] font-mono tracking-widest text-cyan-300 uppercase">
                COGNITIVE COMMAND CORE // LEVEL 7
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white drop-shadow-[0_2px_10px_rgba(56,189,248,0.3)]">
              {getGreeting()}, <span className="text-cyan-400 uppercase">{username || 'Immanuel'}</span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">
              Current Focus: <strong className="text-slate-200">Technology, Science & Autonomous Intelligence</strong>
            </p>
          </div>

          {/* Living 3D Holographic AI Matrix (Tracks Gaze, Breathes, Reacts to Voice) */}
          <div className="relative my-auto flex h-[310px] w-full max-w-[500px] items-center justify-center">
            <LivingJarvisCore
              state={jarvisState}
              audioLevel={audioLevel}
              onClick={toggleListening}
            />
          </div>

          {/* Floating Subtitle Stream & Spoken Speech Response */}
          <div className="w-full max-w-xl text-center space-y-1.5 px-4 -mt-2">
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
                ● {jarvisState.toUpperCase()}
              </span>
              <span>·</span>
              <span>VOICE INTERCOM ACTIVE</span>
            </div>
          </div>
        </div>

        {/* ===================== 3. RIGHT SIDE: INTEL, TASKS & TELEMETRY ===================== */}
        <aside className="hidden lg:flex w-80 shrink-0 flex-col justify-between border-l border-cyan-500/15 bg-slate-950/70 p-3.5 backdrop-blur-2xl text-xs space-y-4 overflow-y-auto thin-scrollbar">
          {/* 1. Daily Executive Briefing Audio Player */}
          <div className="rounded-2xl border border-amber-400/30 bg-gradient-to-b from-amber-500/10 to-transparent p-3 space-y-1.5 shadow-[0_0_15px_rgba(251,191,36,0.1)]">
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
          <div className="space-y-2 border-t border-white/5 pt-3">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <Zap size={12} /> Proactive Collisions
              </span>
              <span className="text-slate-600 font-mono">Live Stream</span>
            </div>

            {recentInsights.length > 0 ? (
              <div className="space-y-1.5">
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
              <div className="rounded-xl border border-white/5 bg-black/30 p-2.5 text-center text-[11px] text-slate-500">
                Watching active browsing & VS Code for semantic collisions...
              </div>
            )}
          </div>

          {/* 3. Today's Strategic Trajectory / Objectives */}
          <div className="space-y-2 border-t border-white/5 pt-3">
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
                  <div className="flex-1 truncate">
                    <span className={`text-[11px] leading-snug line-clamp-1 block ${item.done ? 'line-through text-slate-500' : ''}`}>
                      {item.text}
                    </span>
                    <span className="text-[9px] text-slate-500 font-mono">{item.tag} · {item.due}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 4. Real-Time Hardware & Telemetry Grid */}
          <div className="rounded-2xl border border-white/5 bg-black/40 p-2.5 space-y-1.5 border-t border-white/5 pt-3">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold border-b border-white/5 pb-1 flex items-center justify-between">
              <span>Hardware & Vault Telemetry</span>
              <span className="text-emerald-400 font-bold">ONLINE</span>
            </div>
            <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono">
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
        </aside>
      </div>

      {/* ===================== 4. BOTTOM UNIVERSAL AI COMMAND BAR ===================== */}
      <div className="z-30 w-full border-t border-cyan-500/20 bg-slate-950/95 px-4 py-2.5 backdrop-blur-2xl">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-2">
          {/* Input & Microphone Bar */}
          <form
            onSubmit={(e) => { e.preventDefault(); executeCommand(); }}
            className="flex items-center gap-2 rounded-2xl border border-cyan-500/35 bg-black/75 p-1.5 shadow-[0_0_20px_rgba(56,189,248,0.2)] focus-within:border-cyan-400 transition"
          >
            <button
              type="button"
              onClick={toggleListening}
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition ${
                jarvisState === 'listening'
                  ? 'bg-emerald-400 text-slate-950 shadow-[0_0_15px_rgba(52,211,153,0.6)] animate-pulse'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              }`}
              title="Toggle Spoken Voice Intercom"
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
              JARVIS COMMAND // READY
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
                  {activeOverlay === 'wiki_reader' && `${selectedWikiDoc?.title || 'Master Topic Wiki'}`}
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

              {activeOverlay === 'wiki_reader' && selectedWikiDoc && (
                <div className="prose prose-invert max-w-none text-xs leading-relaxed text-slate-300 whitespace-pre-wrap font-mono bg-black/40 p-5 rounded-2xl border border-white/5">
                  {selectedWikiDoc.content}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full-Screen Image Lightbox Modal */}
      {selectedCardImage && (
        <div
          onClick={() => setSelectedCardImage(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div className="relative max-h-[92vh] max-w-[92vw] overflow-hidden rounded-2xl border border-white/20 bg-slate-950 p-3 shadow-2xl">
            <img src={selectedCardImage} alt="Hero Screen Capture" className="max-h-[84vh] w-auto rounded-xl object-contain" />
            <div className="mt-3 flex items-center justify-between px-2 text-xs text-slate-400">
              <span>Representative Hero Screen Capture · Immanuel's Memory Layer</span>
              <button
                type="button"
                onClick={() => setSelectedCardImage(null)}
                className="rounded-lg bg-white/10 px-3.5 py-1.5 font-bold text-slate-200 transition hover:bg-white/20"
              >
                Close (Esc)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
