import { useEffect, useRef, useState } from 'react';
import { ExternalLink, Mic, MicOff, Volume2, X, Sparkles } from 'lucide-react';
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

  // Force pure 100% alpha transparency on body & root
  useEffect(() => {
    document.documentElement.classList.add('transparent-orb');
    document.body.classList.add('transparent-orb');
    document.documentElement.style.background = 'transparent';
    document.body.style.background = 'transparent';

    return () => {
      document.documentElement.classList.remove('transparent-orb');
      document.body.classList.remove('transparent-orb');
      document.documentElement.style.background = '';
      document.body.style.background = '';
    };
  }, []);

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
    <div className="relative flex h-screen w-screen flex-col items-center justify-between p-2 bg-transparent select-none overflow-hidden">
      {/* Floating Top Controls (Zero background box, drag anywhere on screen) */}
      <div
        style={{ WebkitAppRegion: 'drag' }}
        className="flex w-full items-center justify-between px-2 pt-1 cursor-grab active:cursor-grabbing opacity-75 hover:opacity-100 transition"
      >
        <div className="flex items-center gap-1.5 rounded-full bg-black/40 px-2.5 py-0.5 border border-amber-400/30 backdrop-blur-md">
          <span className="flex h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
          <span className="text-[9px] font-bold tracking-widest text-amber-300 font-mono uppercase">
            JARVIS
          </span>
        </div>

        <div style={{ WebkitAppRegion: 'no-drag' }} className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={openFullApp}
            className="flex h-6 w-6 items-center justify-center rounded-full bg-black/40 text-amber-300/80 hover:bg-black/80 hover:text-amber-200 border border-white/10 transition"
            title="Open Command Center"
          >
            <ExternalLink size={11} />
          </button>
          <button
            type="button"
            onClick={dismissOrb}
            className="flex h-6 w-6 items-center justify-center rounded-full bg-black/40 text-amber-300/80 hover:bg-red-500/80 hover:text-white border border-white/10 transition"
            title="Dismiss (Esc)"
          >
            <X size={12} />
          </button>
        </div>
      </div>

      {/* Pure 3D Golden Holographic Spherical Matrix (No Background Rectangles) */}
      <div className="relative flex flex-1 items-center justify-center my-auto">
        <GoldenJarvisMatrix
          state={orbState}
          audioLevel={audioLevel}
          size={320}
        />
      </div>

      {/* Floating Transparent Subtitle Capsule */}
      <div
        style={{ WebkitAppRegion: 'no-drag' }}
        className="z-20 w-full max-w-[340px] mb-1 flex flex-col items-center text-center"
      >
        {transcript && (
          <p className="text-[11px] text-amber-200/80 italic line-clamp-1 mb-1 px-3 py-0.5 rounded-full bg-black/40 backdrop-blur-md border border-white/5">
            "{transcript}"
          </p>
        )}

        <div className="rounded-2xl border border-amber-400/35 bg-black/45 px-4 py-2.5 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold leading-relaxed text-amber-100 drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]">
            {replyText}
          </p>
          <div className="mt-1 flex items-center justify-center gap-2 text-[9px] text-amber-400/70 font-mono uppercase tracking-wider">
            <span>● {orbState}</span>
            <span>·</span>
            <span>RTX 3050 Memory Core</span>
          </div>
        </div>
      </div>
    </div>
  );
}
