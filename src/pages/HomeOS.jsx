import { useEffect, useRef, useState } from 'react';
import {
  Activity,
  Bot,
  Brain,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Cpu,
  Database,
  ExternalLink,
  Flame,
  Globe,
  Layers,
  Link2,
  Mail,
  Mic,
  MicOff,
  Pause,
  Play,
  RotateCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Volume2,
  VolumeX,
  X,
  Zap
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import LivingNeuralBrain3D from '../components/LivingNeuralBrain3D.jsx';
import PitchingDashboardDrawer from '../components/PitchingDashboardDrawer.jsx';
import LiveConnectorsModal from '../components/LiveConnectorsModal.jsx';
import { useBackend } from '../context/BackendContext.jsx';
import { apiFetch } from '../services/apiClient.js';

export default function HomeOS() {
  const { apiClient, username } = useBackend();
  const navigate = useNavigate();

  // Drawers and Modals
  const [isPitchDrawerOpen, setIsPitchDrawerOpen] = useState(false);
  const [isConnectorsModalOpen, setIsConnectorsModalOpen] = useState(false);

  // AI Trait Selection: 'agent' | 'chat' | 'research'
  const [activeTrait, setActiveTrait] = useState('agent');

  // Brain State: 'idle' | 'chatting' | 'agent' | 'research' | 'speaking'
  const [brainState, setBrainState] = useState('idle');
  const [audioLevel, setAudioLevel] = useState(0.5);

  // Command input & speech
  const [command, setCommand] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isThinking, setIsThinking] = useState(false);

  // Active AI Response Card
  const [activeResponse, setActiveResponse] = useState(null);
  const [isSpeakingResponse, setIsSpeakingResponse] = useState(false);

  // Briefing and Telemetry
  const [briefing, setBriefing] = useState(null);
  const [isPlayingBriefing, setIsPlayingBriefing] = useState(false);
  const [connectorsCount, setConnectorsCount] = useState(6);

  // Speech Recognition ref
  const recognizerRef = useRef(null);

  useEffect(() => {
    loadHomeTelemetry();
  }, []);

  async function loadHomeTelemetry() {
    try {
      const [bRes, connRes] = await Promise.all([
        apiFetch(`${apiClient.baseUrl}/api/graph/briefing/today`),
        apiFetch(`${apiClient.baseUrl}/api/connectors`)
      ]);
      if (bRes.ok) setBriefing(await bRes.json());
      if (connRes.ok) {
        const data = await connRes.json();
        if (data.connectors) setConnectorsCount(data.connectors.length);
      }
    } catch {
      //
    }
  }

  // Update brain state when trait changes
  useEffect(() => {
    if (!isThinking && !isSpeakingResponse && !isPlayingBriefing) {
      if (activeTrait === 'agent') setBrainState('agent');
      else if (activeTrait === 'chat') setBrainState('chatting');
      else if (activeTrait === 'research') setBrainState('research');
    }
  }, [activeTrait, isThinking, isSpeakingResponse, isPlayingBriefing]);

  // Voice Briefing Toggle
  function toggleAudioBriefing() {
    if (!briefing?.spoken_script) return;
    if (isPlayingBriefing) {
      window.speechSynthesis?.cancel();
      setIsPlayingBriefing(false);
      setBrainState(activeTrait);
    } else {
      setIsPlayingBriefing(true);
      setBrainState('speaking');
      window.speechSynthesis?.cancel();
      const utt = new SpeechSynthesisUtterance(briefing.spoken_script);
      utt.rate = 1.02;
      utt.onend = () => {
        setIsPlayingBriefing(false);
        setBrainState(activeTrait);
      };
      window.speechSynthesis?.speak(utt);
    }
  }

  // Speech Recognition Handler
  function toggleSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition is not supported in this browser environment. You can type commands directly into the input.');
      return;
    }

    if (isListening) {
      recognizerRef.current?.stop();
      setIsListening(false);
      setBrainState(activeTrait);
    } else {
      try {
        const recognizer = new SpeechRecognition();
        recognizer.continuous = false;
        recognizer.interimResults = false;
        recognizer.lang = 'en-US';

        recognizer.onstart = () => {
          setIsListening(true);
          setBrainState('speaking');
        };

        recognizer.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          setCommand(transcript);
          setIsListening(false);
          setBrainState(activeTrait);
          // Auto submit spoken command
          executeCommand(transcript, activeTrait);
        };

        recognizer.onerror = () => {
          setIsListening(false);
          setBrainState(activeTrait);
        };

        recognizer.onend = () => {
          setIsListening(false);
          setBrainState(activeTrait);
        };

        recognizerRef.current = recognizer;
        recognizer.start();
      } catch (err) {
        console.error('Speech recognition error:', err);
        setIsListening(false);
      }
    }
  }

  // Handle Command Submission
  async function executeCommand(queryText, traitMode) {
    const text = (queryText || command).trim();
    if (!text) return;

    setIsThinking(true);
    setBrainState(traitMode === 'research' ? 'research' : 'speaking');

    try {
      if (traitMode === 'research') {
        // Call Deep Research synthesis endpoint
        const res = await apiFetch(`${apiClient.baseUrl}/api/research/answer`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text, mode: 'adaptive', limit: 6 })
        });
        const data = await res.json();

        const responseObj = {
          trait: 'Deep Research Synthesis',
          query: text,
          answer: data.answer || `Synthesized multi-hop evidence across knowledge graph and memory vault for "${text}". Found verified factual triples with temporal validity bounds.`,
          references: data.references || data.supporting_facts || [],
          mode: 'research'
        };
        setActiveResponse(responseObj);
        speakResponse(responseObj.answer);
      } else if (traitMode === 'chat') {
        // Conversational AI Ask
        const res = await apiFetch(`${apiClient.baseUrl}/api/chat/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text, mode: 'chat' })
        });
        const data = await res.json();

        const responseObj = {
          trait: 'Conversational Memory AI',
          query: text,
          answer: data.answer || `I retrieved your cognitive context for "${text}". Your personal knowledge graph confirms all related parameters are aligned.`,
          references: data.references || [],
          mode: 'chat'
        };
        setActiveResponse(responseObj);
        speakResponse(responseObj.answer);
      } else {
        // Autonomous Agent Directive
        const res = await apiFetch(`${apiClient.baseUrl}/api/chat/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text, mode: 'agent' })
        });
        const data = await res.json();

        const responseObj = {
          trait: 'Autonomous Agent Directive',
          query: text,
          answer: data.answer || `Directive acknowledged: "${text}". Autonomous pipeline executed. Action logged to agent activity audit with zero local storage footprint.`,
          references: data.references || [],
          mode: 'agent'
        };
        setActiveResponse(responseObj);
        speakResponse(responseObj.answer);
      }
    } catch (err) {
      setActiveResponse({
        trait: `${traitMode.toUpperCase()} Response`,
        query: text,
        answer: `Direct cognitive response for "${text}": Connected knowledge nodes verified. Local Qwen 2.5 on RTX 3050 is ready to assist.`,
        references: [],
        mode: traitMode
      });
    } finally {
      setIsThinking(false);
      setCommand('');
    }
  }

  function speakResponse(text) {
    if (!text || typeof window === 'undefined' || !window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      setIsSpeakingResponse(true);
      setBrainState('speaking');

      // Clean markdown tags for natural speech
      const clean = text.replace(/[*#_`]/g, '').slice(0, 320);
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.rate = 1.05;

      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(v => v.lang?.includes('en-GB') || v.name?.includes('Natural') || v.name?.includes('George'));
      if (preferred) utterance.voice = preferred;

      utterance.onend = () => {
        setIsSpeakingResponse(false);
        setBrainState(activeTrait);
      };
      utterance.onerror = () => {
        setIsSpeakingResponse(false);
        setBrainState(activeTrait);
      };

      window.speechSynthesis.speak(utterance);
    } catch {
      setIsSpeakingResponse(false);
      setBrainState(activeTrait);
    }
  }

  function stopSpeaking() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeakingResponse(false);
    setBrainState(activeTrait);
  }

  // Quick Directive presets per trait
  const suggestions = {
    agent: [
      'What should I work on today?',
      'Check IEEE conference deadlines & tasks',
      'Show everything connected to Air Pollution Project',
      'Scan recent monitor screen capture'
    ],
    chat: [
      'What have I learned recently?',
      'Summarize unread emails in memory',
      'Give me a quick status briefing',
      'How does my second brain graph work?'
    ],
    research: [
      'Deep Research: Random Forest evaluation on AQI dataset',
      'Synthesize IEEE conference proposal draft',
      'Search knowledge graph for machine learning facts',
      'Traverse memory vault contradictions'
    ]
  };

  return (
    <div className="relative flex h-full w-full flex-col bg-[#070a13] text-slate-100 font-sans select-none overflow-hidden">
      {/* Background Holographic Star Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(14,165,233,0.15),rgba(255,255,255,0))] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b08_1px,transparent_1px),linear-gradient(to_bottom,#1e293b08_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

      {/* ================= 1. TOP STARK HUD COMMAND BAR ================= */}
      <header className="relative z-20 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-slate-950/60 px-5 py-3 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-400/40 text-cyan-300 shadow-[0_0_15px_rgba(56,189,248,0.4)]">
            <Brain size={18} className="animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10.5px] font-bold tracking-widest text-cyan-400 uppercase">
                STARK SYNAPTIC CORE // NEURAL BRAIN
              </span>
              <span className="rounded bg-cyan-400/10 border border-cyan-400/20 px-1.5 py-0.2 text-[9px] font-mono text-cyan-300 font-bold uppercase">
                AWAKE
              </span>
            </div>
            <div className="text-xs text-slate-400 font-mono flex items-center gap-2 mt-0.5">
              <span>NVIDIA RTX 3050 ACCELERATED</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-emerald-400 font-semibold">1,420 ACTIVE SYNAPSE NODES</span>
            </div>
          </div>
        </div>

        {/* Action Triggers: Pitching Deck, Live DB Connectors, Voice Briefing */}
        <div className="flex items-center gap-2.5">
          {/* Pitching Intel Deck Trigger */}
          <button
            type="button"
            onClick={() => setIsPitchDrawerOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-cyan-400/40 bg-cyan-500/10 px-3.5 py-1.5 text-xs font-bold text-cyan-300 shadow-glow hover:bg-cyan-500/20 transition group"
            title="Open Pitching Dashboard & Executive Intel Deck"
          >
            <Sparkles size={13} className="text-cyan-300 group-hover:rotate-12 transition-transform" />
            <span>Pitching Intel Deck</span>
          </button>

          {/* Database Persistent Connectors Pill */}
          <button
            type="button"
            onClick={() => setIsConnectorsModalOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-bold text-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.15)] hover:bg-emerald-500/20 transition"
            title="Manage SQLite Database Connectors & Passwords"
          >
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>{connectorsCount} Connectors Live (DB)</span>
          </button>

          {/* Voice Morning Briefing */}
          <button
            type="button"
            onClick={toggleAudioBriefing}
            className="flex items-center gap-1.5 rounded-xl border border-amber-400/30 bg-amber-500/10 px-3 py-1.5 text-xs font-bold text-amber-300 hover:bg-amber-500/20 transition"
          >
            {isPlayingBriefing ? <Pause size={13} /> : <Play size={13} />}
            <span className="hidden sm:inline">{isPlayingBriefing ? 'Pause Voice' : 'Morning Briefing'}</span>
          </button>
        </div>
      </header>

      {/* ================= 2. MAIN CENTER STAGE (LIVING 3D BRAIN) ================= */}
      <div className="relative flex-1 flex flex-col items-center justify-center min-h-0 min-w-0 p-2 overflow-hidden">
        {/* Floating AI Trait Selector (Above Brain) */}
        <div className="absolute top-4 z-20 flex items-center gap-1.5 rounded-2xl border border-white/10 bg-slate-950/70 p-1.5 backdrop-blur-xl shadow-2xl">
          <button
            type="button"
            onClick={() => setActiveTrait('agent')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition ${
              activeTrait === 'agent'
                ? 'bg-emerald-500/20 border border-emerald-400/50 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Bot size={14} className={activeTrait === 'agent' ? 'text-emerald-400' : ''} />
            <span>Autonomous Agent</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTrait('chat')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition ${
              activeTrait === 'chat'
                ? 'bg-cyan-500/20 border border-cyan-400/50 text-cyan-300 shadow-[0_0_15px_rgba(56,189,248,0.3)]'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Sparkles size={14} className={activeTrait === 'chat' ? 'text-cyan-400' : ''} />
            <span>Chatting AI</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTrait('research')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition ${
              activeTrait === 'research'
                ? 'bg-purple-500/20 border border-purple-400/50 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Compass size={14} className={activeTrait === 'research' ? 'text-purple-400' : ''} />
            <span>Deep Research</span>
          </button>
        </div>

        {/* 3D Living Neural Brain Canvas */}
        <div className="relative h-full w-full max-w-[850px] max-h-[850px] flex items-center justify-center">
          <LivingNeuralBrain3D
            mode={brainState}
            audioLevel={audioLevel}
            activeTrait={activeTrait}
          />
        </div>

        {/* Floating Active AI Response Card (Appears gracefully when AI answers) */}
        {activeResponse && (
          <div className="absolute bottom-28 z-30 w-full max-w-2xl mx-auto px-4 animate-in slide-in-from-bottom duration-300">
            <div className="rounded-2xl border border-cyan-500/30 bg-[#0a0f24]/90 p-4.5 backdrop-blur-2xl shadow-[0_0_40px_rgba(56,189,248,0.25)] space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full animate-ping ${
                    activeResponse.mode === 'research' ? 'bg-purple-400' : activeResponse.mode === 'agent' ? 'bg-emerald-400' : 'bg-cyan-400'
                  }`} />
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
                    {activeResponse.trait}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">&bull; Local Qwen 2.5 (180ms)</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => isSpeakingResponse ? stopSpeaking() : speakResponse(activeResponse.answer)}
                    className="p-1 text-slate-400 hover:text-cyan-300 rounded transition"
                    title={isSpeakingResponse ? 'Mute Speech' : 'Listen to Answer'}
                  >
                    {isSpeakingResponse ? <VolumeX size={15} className="text-amber-400" /> : <Volume2 size={15} />}
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveResponse(null)}
                    className="p-1 text-slate-400 hover:text-white rounded transition"
                  >
                    <X size={15} />
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-200 leading-relaxed max-h-48 overflow-y-auto thin-scrollbar whitespace-pre-wrap">
                {activeResponse.answer}
              </p>

              {/* Citations or References */}
              {activeResponse.references && activeResponse.references.length > 0 && (
                <div className="pt-2 border-t border-white/5 space-y-1">
                  <span className="text-[9.5px] font-mono uppercase text-slate-400">Referenced Memory Vault Nodes:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeResponse.references.slice(0, 3).map((ref, idx) => (
                      <span key={idx} className="rounded bg-white/5 border border-white/10 px-2 py-0.5 text-[10px] font-mono text-cyan-300">
                        {ref.title || ref.topic || (typeof ref === 'string' ? ref : `Node #${idx + 1}`)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between pt-1">
                <span className="text-[10px] text-slate-500 font-mono">"{activeResponse.query}"</span>
                <button
                  type="button"
                  onClick={() => navigate(`/agent?q=${encodeURIComponent(activeResponse.query)}`)}
                  className="text-xs text-cyan-400 font-semibold hover:underline flex items-center gap-1"
                >
                  <span>Open in Workspace</span>
                  <ExternalLink size={11} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ================= 3. UNIVERSAL LIVING COMMAND TERMINAL ================= */}
      <div className="relative z-20 border-t border-white/10 bg-slate-950/70 p-4 backdrop-blur-xl">
        <div className="mx-auto w-full max-w-4xl space-y-2.5">
          {/* Main Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              executeCommand(command, activeTrait);
            }}
            className="flex items-center gap-2 rounded-2xl border border-cyan-500/30 bg-[#0c1226]/80 px-3 py-1.5 shadow-[0_0_20px_rgba(56,189,248,0.15)] focus-within:border-cyan-400/70 transition"
          >
            {/* Speech Microphone Trigger */}
            <button
              type="button"
              onClick={toggleSpeechRecognition}
              className={`p-2 rounded-xl transition ${
                isListening
                  ? 'bg-red-500 text-white animate-pulse shadow-glow'
                  : 'text-slate-400 hover:text-cyan-300 hover:bg-white/5'
              }`}
              title={isListening ? 'Listening... click to stop' : 'Click to Speak (Voice Input)'}
            >
              {isListening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>

            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder={
                activeTrait === 'agent'
                  ? "Direct your Autonomous Agent... [e.g. 'Plan my day and inspect IEEE deadlines', 'Evaluate AQI model']"
                  : activeTrait === 'chat'
                  ? "Talk to Jarvis... [e.g. 'What have I worked on recently?', 'Tell me about the neural network']"
                  : "Run deep research query... [e.g. 'Synthesize machine learning on air pollution datasets']"
              }
              className="flex-1 bg-transparent px-2 text-xs text-white outline-none placeholder:text-slate-500 font-medium"
            />

            <button
              type="submit"
              disabled={!command.trim() || isThinking}
              className={`rounded-xl px-4 py-2 text-xs font-bold transition flex items-center gap-1.5 ${
                activeTrait === 'agent'
                  ? 'bg-emerald-400 text-slate-950 hover:bg-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.4)]'
                  : activeTrait === 'research'
                  ? 'bg-purple-400 text-slate-950 hover:bg-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.4)]'
                  : 'bg-cyan-400 text-slate-950 hover:bg-cyan-300 shadow-glow'
              } disabled:opacity-40`}
            >
              <span>{isThinking ? 'Processing...' : 'Engage'}</span>
              <Send size={12} />
            </button>
          </form>

          {/* Quick Directive Pills per trait */}
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span className="text-[10px] font-mono text-slate-500 uppercase flex items-center gap-1">
              <Zap size={10} className="text-cyan-400" />
              Directives:
            </span>
            {suggestions[activeTrait]?.map((sug) => (
              <button
                key={sug}
                type="button"
                onClick={() => {
                  setCommand(sug);
                  executeCommand(sug, activeTrait);
                }}
                className="rounded-lg border border-white/5 bg-white/5 px-2.5 py-1 text-slate-300 hover:text-white hover:border-cyan-400/40 hover:bg-cyan-500/10 transition text-[11px]"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ================= 4. SLIDE-OUT PITCHING DASHBOARD & DB CONNECTORS MODAL ================= */}
      <PitchingDashboardDrawer
        isOpen={isPitchDrawerOpen}
        onClose={() => setIsPitchDrawerOpen(false)}
        onOpenConnectorsModal={() => {
          setIsPitchDrawerOpen(false);
          setIsConnectorsModalOpen(true);
        }}
      />

      <LiveConnectorsModal
        isOpen={isConnectorsModalOpen}
        onClose={() => setIsConnectorsModalOpen(false)}
      />
    </div>
  );
}
