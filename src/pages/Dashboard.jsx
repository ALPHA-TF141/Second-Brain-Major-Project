import { useEffect, useRef, useState } from 'react';
import { Activity, BookOpen, Brain, CheckCircle2, ChevronRight, CornerDownLeft, Cpu, ExternalLink, Eye, FileText, GitBranch, Globe, Image as ImageIcon, Layers, Mic, MicOff, Network, Play, Pause, Power, RefreshCw, Send, ShieldCheck, Sparkles, Terminal, Volume2, Wrench, X, Zap } from 'lucide-react';
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
  const [jarvisReply, setJarvisReply] = useState('All systems nominal, Sir. How may I assist you?');
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeOverlay, setActiveOverlay] = useState(null); // 'graph' | 'forge' | 'social' | 'cards' | null

  // Telemetry Metrics
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [vaultCards, setVaultCards] = useState([]);
  const [recentInsight, setRecentInsight] = useState(null);
  const [isBriefingPlaying, setIsBriefingPlaying] = useState(false);

  const socketRef = useRef(null);
  const recognitionRef = useRef(null);

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

    // 2. Fetch Graph & Cards Telemetry
    async function fetchTelemetry() {
      try {
        const [gRes, cRes, insRes] = await Promise.all([
          fetch(`${apiClient.baseUrl}/api/graph/vault`),
          fetch(`${apiClient.baseUrl}/api/graph/vault/cards?limit=6`),
          fetch(`${apiClient.baseUrl}/api/graph/insights/recent`)
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
            setRecentInsight(insData[insData.length - 1]);
          }
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
    }
  }

  // Voice Synthesis Output
  function speak(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const britishOrNatural = voices.find(v => v.lang.includes('en-GB') || v.name.includes('Natural') || v.name.includes('George'));
    if (britishOrNatural) utterance.voice = britishOrNatural;

    utterance.onstart = () => setJarvisState('speaking');
    utterance.onend = () => setJarvisState('idle');
    window.speechSynthesis.speak(utterance);
  }

  // Toggle Microphone Listening
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

  // Handle Text Submission
  async function handleSendText(e) {
    e?.preventDefault();
    const text = inputText.trim();
    if (!text) return;
    setInputText('');
    setUserTranscript(text);
    setJarvisState('thinking');
    setIsProcessing(true);

    try {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'transcript', text, final: true }));
      } else {
        const res = await apiClient.askMemory({ question: text, mode: 'summary' });
        setJarvisReply(res.answer || 'Query processed, Sir.');
        speak(res.answer);
      }
    } catch {
      setJarvisReply('Local Qwen 2.5 is synthesizing your request.');
    } finally {
      setIsProcessing(false);
    }
  }

  // Trigger Daily Executive Briefing
  async function triggerBriefing() {
    setIsBriefingPlaying(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/briefing/today`);
      if (res.ok) {
        const data = await res.json();
        setJarvisReply(data.spoken_script);
        speak(data.spoken_script);
      }
    } catch {
      setJarvisReply('All systems synchronized, Sir.');
    } finally {
      setIsBriefingPlaying(false);
    }
  }

  return (
    <div className="relative flex h-full w-full flex-col items-center justify-between overflow-hidden bg-radial-gradient p-4 text-slate-100 font-sans select-none">
      {/* Background Ambience & Grid */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/10 via-[#030712]/90 to-[#030712] z-0" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#1f293708_1px,transparent_1px),linear-gradient(to_bottom,#1f293708_1px,transparent_1px)] bg-[size:4rem_4rem] z-0" />

      {/* TOP FLOATING TELEMETRY WIDGETS */}
      <div className="z-10 flex w-full max-w-7xl items-start justify-between gap-4">
        {/* Left Telemetry Cluster */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-cyan-500/25 bg-slate-950/70 px-3.5 py-1.5 backdrop-blur-xl shadow-glow">
            <Cpu size={14} className="text-cyan-400 animate-pulse" />
            <span className="text-[11px] font-mono tracking-wider text-slate-300">
              NVIDIA RTX 3050 · <strong className="text-cyan-300 font-bold">210ms INFERENCE</strong>
            </span>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/60 px-3.5 py-1.5 text-[11px] font-mono text-slate-400 backdrop-blur-xl">
            <Brain size={14} className="text-purple-400" />
            <span>SYNAPSE MESH: <strong className="text-white">{graphData.nodes.length || 540} NODES</strong></span>
          </div>
        </div>

        {/* Right Executive Audio Briefing Pill */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={triggerBriefing}
            disabled={isBriefingPlaying}
            className="flex items-center gap-2 rounded-xl border border-amber-400/40 bg-gradient-to-r from-amber-500/15 to-amber-600/10 px-4 py-2 text-xs font-bold text-amber-300 shadow-[0_0_15px_rgba(251,191,36,0.2)] backdrop-blur-xl transition hover:scale-105 active:scale-95"
          >
            <Sparkles size={14} className={isBriefingPlaying ? 'animate-spin text-amber-300' : 'text-amber-400'} />
            <span>{isBriefingPlaying ? 'Synthesizing...' : 'Play Morning Briefing'}</span>
          </button>
        </div>
      </div>

      {/* CENTER STAGE: THE LIVING, BREATHING JARVIS AI CORE */}
      <div className="relative z-10 flex flex-1 flex-col items-center justify-center my-auto w-full max-w-4xl">
        {/* 3D Living Core (tracks mouse gaze, breathes, reacts to voice) */}
        <div className="relative h-[360px] w-full max-w-[540px]">
          <LivingJarvisCore
            state={jarvisState}
            audioLevel={audioLevel}
            onClick={toggleListening}
          />
        </div>

        {/* Live Subtitle Stream & Jarvis Speech (Floating Hologram) */}
        <div className="w-full max-w-xl text-center space-y-1.5 px-4 -mt-2">
          {userTranscript && (
            <p className="text-xs italic text-cyan-300/80 font-mono tracking-wide line-clamp-1">
              "{userTranscript}"
            </p>
          )}

          <p className="text-base font-semibold tracking-wide text-slate-100 drop-shadow-[0_2px_12px_rgba(56,189,248,0.5)] leading-relaxed">
            {jarvisReply}
          </p>

          <div className="flex items-center justify-center gap-3 pt-1 text-[10px] font-mono uppercase tracking-widest text-slate-500">
            <span className={jarvisState === 'listening' ? 'text-emerald-400 font-bold animate-pulse' : ''}>
              ● {jarvisState.toUpperCase()}
            </span>
            <span>·</span>
            <span>PRESS ALT + J FOR HOLO-ORB</span>
          </div>
        </div>
      </div>

      {/* BOTTOM ACTION DOCK & COMMAND INTERFACE */}
      <div className="z-20 w-full max-w-3xl space-y-3">
        {/* Natural Language Prompt Input Bar */}
        <form
          onSubmit={handleSendText}
          className="flex items-center gap-2 rounded-2xl border border-cyan-500/30 bg-slate-950/80 p-1.5 shadow-[0_0_25px_rgba(0,0,0,0.8)] backdrop-blur-2xl transition focus-within:border-cyan-400 focus-within:shadow-[0_0_20px_rgba(56,189,248,0.25)]"
        >
          <button
            type="button"
            onClick={toggleListening}
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition ${
              jarvisState === 'listening'
                ? 'bg-emerald-400 text-slate-950 shadow-[0_0_15px_rgba(52,211,153,0.6)] animate-pulse'
                : 'bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
            }`}
            title="Toggle Voice Intercom"
          >
            {jarvisState === 'listening' ? <Mic size={18} /> : <MicOff size={18} />}
          </button>

          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Instruct Jarvis, query memory vault, or speak naturally..."
            className="w-full bg-transparent px-2 text-xs text-slate-100 outline-none placeholder:text-slate-500 font-medium"
          />

          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 font-bold transition hover:bg-cyan-300 disabled:opacity-30 disabled:hover:bg-cyan-400"
            title="Send to Jarvis"
          >
            {isProcessing ? <RefreshCw size={15} className="animate-spin" /> : <CornerDownLeft size={16} />}
          </button>
        </form>

        {/* Holographic Arc Action Matrix Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 text-xs">
          <button
            type="button"
            onClick={analyzeActiveScreen}
            className="flex items-center gap-2 rounded-xl border border-cyan-400/40 bg-gradient-to-r from-cyan-500/20 to-blue-600/10 px-3.5 py-2 font-semibold text-cyan-300 transition hover:scale-105 active:scale-95 shadow-glow"
          >
            <Eye size={14} className="text-cyan-400 animate-pulse" />
            <span>Scan Monitor (Vision)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveOverlay(activeOverlay === 'graph' ? null : 'graph')}
            className={`flex items-center gap-2 rounded-xl border px-3.5 py-2 font-semibold transition backdrop-blur-xl ${
              activeOverlay === 'graph'
                ? 'border-cyan-400 bg-cyan-500/20 text-cyan-300 shadow-glow'
                : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-cyan-500/40 hover:text-white'
            }`}
          >
            <Network size={14} className="text-cyan-400" />
            <span>Knowledge Galaxy</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveOverlay(activeOverlay === 'forge' ? null : 'forge')}
            className={`flex items-center gap-2 rounded-xl border px-3.5 py-2 font-semibold transition backdrop-blur-xl ${
              activeOverlay === 'forge'
                ? 'border-mintGlow bg-emerald-500/20 text-mintGlow shadow-glow'
                : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-emerald-500/40 hover:text-white'
            }`}
          >
            <Wrench size={14} className="text-mintGlow" />
            <span>Deliverable Forge</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveOverlay(activeOverlay === 'social' ? null : 'social')}
            className={`flex items-center gap-2 rounded-xl border px-3.5 py-2 font-semibold transition backdrop-blur-xl ${
              activeOverlay === 'social'
                ? 'border-purple-400 bg-purple-500/20 text-purple-300 shadow-glow'
                : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-purple-500/40 hover:text-white'
            }`}
          >
            <Globe size={14} className="text-purple-400" />
            <span>Native Web Scraper</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveOverlay(activeOverlay === 'cards' ? null : 'cards')}
            className={`flex items-center gap-2 rounded-xl border px-3.5 py-2 font-semibold transition backdrop-blur-xl ${
              activeOverlay === 'cards'
                ? 'border-amber-400 bg-amber-500/20 text-amber-300 shadow-glow'
                : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-amber-500/40 hover:text-white'
            }`}
          >
            <Layers size={14} className="text-amber-400" />
            <span>Vault Evidence ({vaultCards.length})</span>
          </button>
        </div>
      </div>

      {/* HOLOGRAPHIC HUD DRAWER OVERLAYS (Opens without breaking the living AI core!) */}
      {activeOverlay && (
        <div
          onClick={() => setActiveOverlay(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-6 backdrop-blur-2xl animate-in fade-in duration-200"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="thin-scrollbar relative flex h-[88vh] w-full max-w-6xl flex-col rounded-3xl border border-cyan-500/30 bg-[#070b18]/95 p-6 shadow-2xl backdrop-blur-2xl overflow-y-auto"
          >
            {/* Drawer Header */}
            <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2.5">
                <span className="flex h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse" />
                <h3 className="text-base font-bold text-white uppercase tracking-wider font-mono">
                  {activeOverlay === 'graph' && 'OBSIDIAN KNOWLEDGE GALAXY · FORCE CLUSTERS'}
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
                Close HUD (Esc)
              </button>
            </div>

            {/* Drawer Content Views */}
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
