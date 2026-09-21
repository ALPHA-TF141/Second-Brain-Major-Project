import { useEffect, useRef, useState } from 'react';
import { ExternalLink, Mic, MicOff, Minus, Volume2, X, Sparkles } from 'lucide-react';
import GoldenJarvisMatrix from '../components/GoldenJarvisMatrix.jsx';
import { createVoiceSocket } from '../services/voiceSocket.js';
import { apiClient } from '../services/apiClient.js';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

export default function JarvisHoloOrb() {
  const [orbState, setOrbState] = useState('listening'); // 'listening' | 'thinking' | 'speaking' | 'idle'
  const [transcript, setTranscript] = useState('');
  const [replyText, setReplyText] = useState('Listening, Sir...');
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0.5);
  const socketRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize Voice Connection & Wake Word handling
  useEffect(() => {
    let active = true;

    async function initOrbVoice() {
      try {
        if (!apiClient.getToken()) {
          await apiClient.login('demo', 'secondbrain');
        }

        const socket = await createVoiceSocket({
          onOpen: () => {
            socket.send(JSON.stringify({ type: 'start', mode: 'continuous', language: 'mixed' }));
          },
          onEvent: (event) => {
            if (!active) return;
            if (event.type === 'transcript') {
              setTranscript(event.text);
              setOrbState('thinking');
            } else if (event.type === 'speaking') {
              setOrbState(event.status === 'started' ? 'speaking' : 'listening');
            } else if (event.type === 'answer') {
              setReplyText(event.text);
              speakSpeech(event.text);
            }
          }
        });
        socketRef.current = socket;

        // Start Browser Speech Recognition if available
        if (SpeechRecognition) {
          const rec = new SpeechRecognition();
          rec.continuous = true;
          rec.interimResults = true;
          rec.onresult = (e) => {
            let interim = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
              const text = e.results[i][0].transcript;
              if (e.results[i].isFinal) {
                setTranscript(text);
                setOrbState('thinking');
                socketRef.current?.send(JSON.stringify({ type: 'transcript', text, final: true }));
              } else {
                interim += text;
              }
            }
            if (interim) setTranscript(interim);
          };
          rec.start();
          recognitionRef.current = rec;
        }
      } catch (err) {
        console.warn('Orb Voice init error:', err);
      }
    }

    initOrbVoice();

    // Listen for wake IPC event
    const ipc = window.secondBrain;
    if (ipc?.onWakeTrigger) {
      ipc.onWakeTrigger(() => {
        setOrbState('listening');
        setReplyText('Yes, Sir? How can I assist you?');
        speakSpeech('Yes, Sir? How can I assist you?');
      });
    }

    return () => {
      active = false;
      socketRef.current?.close();
      recognitionRef.current?.stop();
    };
  }, []);

  function speakSpeech(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const naturalVoice = voices.find(v => v.lang.includes('en-GB') || v.name.includes('Natural') || v.name.includes('George'));
    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => setOrbState('speaking');
    utterance.onend = () => {
      setOrbState('listening');
      // Auto-collapse after 5 seconds of inactivity
      setTimeout(() => {
        if (window.secondBrain?.hideOrb) {
          window.secondBrain.hideOrb();
        }
      }, 5000);
    };
    window.speechSynthesis.speak(utterance);
  }

  function dismissOrb() {
    window.speechSynthesis?.cancel();
    if (window.secondBrain?.hideOrb) {
      window.secondBrain.hideOrb();
    } else {
      window.close();
    }
  }

  function openFullApp() {
    window.secondBrain?.showMain?.();
    dismissOrb();
  }

  return (
    <div className="relative flex h-screen w-screen flex-col items-center justify-between p-4 bg-transparent select-none overflow-hidden">
      {/* Top Draggable Bar (Allows moving orb anywhere on screen) */}
      <div
        style={{ WebkitAppRegion: 'drag' }}
        className="flex w-full items-center justify-between px-3 py-1 cursor-grab active:cursor-grabbing"
      >
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-amber-400 animate-ping" />
          <span className="text-[10px] font-bold tracking-widest text-amber-300 font-mono uppercase">
            JARVIS HOLO-ORB · ONLINE
          </span>
        </div>

        <div style={{ WebkitAppRegion: 'no-drag' }} className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={openFullApp}
            className="flex h-6 w-6 items-center justify-center rounded-full bg-black/50 text-amber-300/80 hover:bg-black/80 hover:text-amber-200 transition"
            title="Open Full Second Brain Dashboard"
          >
            <ExternalLink size={12} />
          </button>
          <button
            type="button"
            onClick={dismissOrb}
            className="flex h-6 w-6 items-center justify-center rounded-full bg-black/50 text-amber-300/80 hover:bg-red-500/80 hover:text-white transition"
            title="Dismiss Orb (Esc)"
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Center 3D Golden Holographic Spherical Matrix */}
      <div className="relative flex flex-1 items-center justify-center my-auto">
        <GoldenJarvisMatrix
          state={orbState}
          audioLevel={audioLevel}
          size={360}
        />
      </div>

      {/* Bottom Floating Subtitle HUD Card */}
      <div
        style={{ WebkitAppRegion: 'no-drag' }}
        className="z-20 w-full max-w-[440px] rounded-2xl border border-amber-400/40 bg-black/85 p-3.5 shadow-2xl backdrop-blur-2xl"
      >
        <div className="flex items-center justify-between mb-1.5 text-[10px] font-mono uppercase tracking-wider text-amber-400">
          <span className="flex items-center gap-1.5">
            <Sparkles size={11} /> {orbState}
          </span>
          <span className="text-slate-500">{transcript ? 'Hearing input...' : 'Wake: "Hey Jarvis"'}</span>
        </div>

        {transcript && (
          <p className="text-xs text-slate-400 italic line-clamp-1 mb-1">
            "{transcript}"
          </p>
        )}

        <p className="text-xs font-medium leading-relaxed text-amber-100">
          {replyText}
        </p>

        <div className="mt-2.5 flex items-center justify-between border-t border-white/10 pt-2 text-[10px] text-slate-500 font-mono">
          <span>Local RTX 3050 · Private Memory Layer</span>
          <button
            type="button"
            onClick={() => setIsMuted(!isMuted)}
            className="flex items-center gap-1 text-amber-300/80 hover:text-amber-200"
          >
            {isMuted ? <MicOff size={11} /> : <Mic size={11} />}
            <span>{isMuted ? 'Muted' : 'Mic Live'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
