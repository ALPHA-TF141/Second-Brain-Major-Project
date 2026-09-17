import { useEffect, useMemo, useRef, useState } from 'react';
import { Mic2, Pause, Radio, Save, Settings2, Square, Volume2, Waves } from 'lucide-react';
import NeuralBrain3D from '../components/NeuralBrain3D.jsx';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';
import { createVoiceSocket } from '../services/voiceSocket.js';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function VoiceAssistant() {
  const { apiClient, loginDemo } = useBackend();
  const [status, setStatus] = useState('standby');
  const [socketStatus, setSocketStatus] = useState('disconnected');
  const [sessionId, setSessionId] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [partialTranscript, setPartialTranscript] = useState('');
  const [history, setHistory] = useState([]);
  const [voiceStatus, setVoiceStatus] = useState({});
  const [preferences, setPreferences] = useState({
    preferred_language: 'mixed',
    reply_language: 'auto',
    wake_words: 'Second Brain,Hey Brain',
    voice_speed: 1,
    microphone_name: '',
    voice_model: 'default'
  });
  const [mode, setMode] = useState('continuous');
  const socketRef = useRef(null);
  const recorderRef = useRef(null);
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);

  const isListening = status === 'listening';
  const isSpeaking = status === 'speaking';
  const supportsSpeechRecognition = Boolean(SpeechRecognition);

  const languageCode = useMemo(() => {
    if (preferences.preferred_language === 'ta') return 'ta-IN';
    if (preferences.preferred_language === 'en') return 'en-US';
    return 'en-IN';
  }, [preferences.preferred_language]);

  async function ensureLogin() {
    await loginDemo();
  }

  async function loadVoiceMeta() {
    if (!apiClient.getToken()) return;
    apiClient.voiceStatus().then(setVoiceStatus).catch(() => setVoiceStatus({}));
    apiClient.fetchVoicePreferences().then(setPreferences).catch(() => {});
  }

  async function connectSocket() {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      return socketRef.current;
    }
    socketRef.current?.close();
    const socket = await createVoiceSocket({
      onOpen: () => setSocketStatus('connected'),
      onClose: () => setSocketStatus('disconnected'),
      onError: () => setSocketStatus('error'),
      onEvent: handleVoiceEvent
    });
    socketRef.current = socket;
    return socket;
  }

  function handleVoiceEvent(event) {
    if (event.type === 'session') {
      setSessionId(event.session_id);
      return;
    }
    if (event.type === 'transcript') {
      setHistory((current) => [...current, { speaker: event.speaker, text: event.text }].slice(-40));
      return;
    }
    if (event.type === 'intent') {
      setHistory((current) => [...current, { speaker: 'system', text: `Intent: ${event.intent}` }].slice(-40));
      return;
    }
    if (event.type === 'speaking') {
      setStatus(event.status === 'started' ? 'speaking' : 'listening');
      return;
    }
    if (event.type === 'answer') {
      setHistory((current) => [...current, { speaker: 'assistant', text: event.text, references: event.references }].slice(-40));
      speakFallback(event.text);
    }
  }

  function speakFallback(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = preferences.reply_language === 'ta' ? 'ta-IN' : preferences.reply_language === 'en' ? 'en-US' : languageCode;
    utterance.rate = Number(preferences.voice_speed || 1);
    utterance.onstart = () => setStatus('speaking');
    utterance.onend = () => setStatus('listening');
    window.speechSynthesis.speak(utterance);
  }

  async function startListening() {
    await ensureLogin();
    const socket = await connectSocket();

    // Ensure socket is open before sending start
    if (socket && socket.readyState !== WebSocket.OPEN) {
      await new Promise((resolve) => {
        socket.addEventListener('open', resolve, { once: true });
        setTimeout(resolve, 1000);
      });
    }

    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'start', mode, language: preferences.preferred_language }));
    }

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = mediaStream;
      const recorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
          const audio = await blobToBase64(event.data);
          socketRef.current.send(JSON.stringify({ type: 'audio', audio }));
        }
      };
      recorder.start(1200);
      recorderRef.current = recorder;
      startBrowserRecognition();
      setStatus('listening');
    } catch (err) {
      console.warn('Microphone error in Electron:', err);
      // Still set status listening if user wants to use manual transcript
      setStatus('listening');
    }
  }

  function startBrowserRecognition() {
    if (!supportsSpeechRecognition) return;
    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = languageCode;
      recognition.onresult = (event) => {
        let interim = '';
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          const text = event.results[index][0].transcript;
          if (event.results[index].isFinal) {
            setTranscript(text);
            socketRef.current?.send(JSON.stringify({ type: 'transcript', text, final: true }));
          } else {
            interim += text;
          }
        }
        setPartialTranscript(interim);
      };
      recognition.onerror = (err) => {
        console.warn('SpeechRecognition error (expected in standard Electron):', err);
      };
      recognition.onend = () => {
        if (status === 'listening') {
          try {
            recognition.start();
          } catch {
            // Browser may reject restart
          }
        }
      };
      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.warn('SpeechRecognition initialization error:', e);
    }
  }

  function stopListening() {
    recorderRef.current?.stop();
    recognitionRef.current?.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    socketRef.current?.send(JSON.stringify({ type: 'stop' }));
    setStatus('standby');
  }

  async function savePreferences() {
    await ensureLogin();
    const next = await apiClient.updateVoicePreferences(preferences);
    setPreferences(next);
  }

  async function sendManualTranscript() {
    const text = transcript.trim();
    if (!text) return;

    let socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      socket = await connectSocket();
      if (socket && socket.readyState !== WebSocket.OPEN) {
        await new Promise((resolve) => {
          socket.addEventListener('open', resolve, { once: true });
          setTimeout(resolve, 800);
        });
      }
    }

    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'transcript', text, final: true }));
      setTranscript('');
    } else {
      console.error('Socket is not open. Could not send manual transcript.');
    }
  }

  useEffect(() => {
    loadVoiceMeta();
    connectSocket();
    return () => {
      recorderRef.current?.stop();
      recognitionRef.current?.stop();
      streamRef.current?.getTracks().forEach((track) => track.stop());
      socketRef.current?.close();
    };
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Voice Assistant"
        title="Tamil voice cognitive companion"
        description="Realtime microphone streaming, Tamil-English conversation, wake phrases, command routing, memory-aware answers, and spoken replies."
      />

      <div className="grid gap-5 xl:grid-cols-[1.1fr_1.1fr_0.8fr]">
        <section className="glass-panel flex flex-col justify-between rounded-lg p-5">
          <NeuralBrain3D
            state={status === 'listening' ? 'listening' : status === 'speaking' ? 'speaking' : 'idle'}
            domainFocus="Active Sensory Audio Stream"
          />

          <div className="mt-4 flex flex-col items-center justify-center rounded-lg border border-white/10 bg-slate-950/40 p-4">
            <h3 className="text-xl font-semibold capitalize">{status}</h3>
            <p className="mt-1 text-xs text-slate-500">Socket {socketStatus} · Session {sessionId || '-'}</p>

            <div className="mt-4 flex flex-wrap justify-center gap-3">
              <button type="button" onClick={startListening} disabled={isListening} className="flex items-center gap-2 rounded-lg bg-mintGlow px-5 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-emerald-300 disabled:opacity-40">
                <Radio size={16} />
                Start
              </button>
              <button type="button" onClick={() => setStatus('paused')} disabled={!isListening} className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-semibold text-slate-200 transition hover:bg-white/10 disabled:opacity-40">
                <Pause size={16} />
                Pause
              </button>
              <button type="button" onClick={stopListening} disabled={status === 'standby'} className="flex items-center gap-2 rounded-lg border border-red-400/30 bg-red-500/10 px-5 py-2.5 text-sm font-semibold text-red-200 transition hover:bg-red-500/20 disabled:opacity-40">
                <Square size={16} />
                Stop
              </button>
            </div>
          </div>
        </section>

        <section className="glass-panel rounded-lg p-5">
          <div className="mb-4 flex items-center gap-2">
            <Waves size={18} className="text-cyanGlow" />
            <h3 className="font-semibold">Realtime Conversation</h3>
          </div>
          <div className="mb-4 rounded-lg border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase text-slate-500">Live transcript</p>
            <p className="mt-2 min-h-12 text-sm leading-6 text-slate-200">{partialTranscript || transcript || 'Start speaking in Tamil, English, or both.'}</p>
            <div className="mt-3 flex gap-2">
              <input
                value={transcript}
                onChange={(event) => setTranscript(event.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') sendManualTranscript(); }}
                placeholder="Manual transcript fallback..."
                className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm outline-none"
              />
              <button type="button" onClick={sendManualTranscript} className="rounded-lg bg-cyanGlow px-3 py-2 text-sm font-bold text-slate-950">Send</button>
            </div>
          </div>
          <div className="thin-scrollbar max-h-[520px] space-y-3 overflow-y-auto">
            {history.map((item, index) => (
              <div key={index} className={`rounded-lg border p-3 ${item.speaker === 'assistant' ? 'border-cyanGlow/20 bg-cyanGlow/10' : item.speaker === 'system' ? 'border-warningGlow/20 bg-warningGlow/10' : 'border-white/10 bg-white/5'}`}>
                <p className="text-xs uppercase text-slate-500">{item.speaker}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-200">{item.text}</p>
              </div>
            ))}
          </div>
        </section>

        <aside className="space-y-5">
          <section className="glass-panel rounded-lg p-5">
            <div className="mb-4 flex items-center gap-2">
              <Settings2 size={18} className="text-mintGlow" />
              <h3 className="font-semibold">Voice Settings</h3>
            </div>
            <div className="space-y-3">
              <select value={mode} onChange={(event) => setMode(event.target.value)} className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm outline-none">
                <option value="continuous">Continuous</option>
                <option value="push_to_talk">Push to Talk</option>
                <option value="wake_word">Wake Word</option>
              </select>
              <select value={preferences.preferred_language} onChange={(event) => setPreferences((current) => ({ ...current, preferred_language: event.target.value }))} className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm outline-none">
                <option value="mixed">Tamil + English</option>
                <option value="ta">Tamil</option>
                <option value="en">English</option>
              </select>
              <select value={preferences.reply_language} onChange={(event) => setPreferences((current) => ({ ...current, reply_language: event.target.value }))} className="w-full rounded-lg border border-white/10 bg-slate-950/70 px-3 py-2 text-sm outline-none">
                <option value="auto">Reply Auto</option>
                <option value="ta">Reply Tamil</option>
                <option value="en">Reply English</option>
                <option value="mixed">Reply Mixed</option>
              </select>
              <input value={preferences.wake_words} onChange={(event) => setPreferences((current) => ({ ...current, wake_words: event.target.value }))} className="w-full rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm outline-none" />
              <label className="block text-sm text-slate-400">
                Voice speed
                <input type="range" min="0.7" max="1.3" step="0.05" value={preferences.voice_speed} onChange={(event) => setPreferences((current) => ({ ...current, voice_speed: Number(event.target.value) }))} className="mt-2 w-full accent-cyanGlow" />
              </label>
              <button type="button" onClick={savePreferences} className="flex w-full items-center justify-center gap-2 rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 px-3 py-2 text-sm font-semibold text-cyanGlow transition hover:bg-cyanGlow/20">
                <Save size={16} />
                Save Settings
              </button>
            </div>
          </section>

          <section className="glass-panel rounded-lg p-5">
            <div className="mb-4 flex items-center gap-2">
              <Volume2 size={18} className="text-warningGlow" />
              <h3 className="font-semibold">Engine Status</h3>
            </div>
            <div className="space-y-2 text-sm text-slate-400">
              <p>Whisper: {voiceStatus.whisper_ready ? 'ready' : 'optional'}</p>
              <p>Coqui TTS: {voiceStatus.tts_ready ? 'ready' : 'browser voice fallback'}</p>
              <p>Browser STT: {supportsSpeechRecognition ? 'available' : 'manual transcript fallback'}</p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

export default VoiceAssistant;
