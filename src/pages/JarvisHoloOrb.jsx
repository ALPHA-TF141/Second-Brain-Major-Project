import { useCallback, useEffect, useRef, useState } from 'react';
import { ExternalLink, MicOff, X } from 'lucide-react';
import GoldenJarvisMatrix from '../components/GoldenJarvisMatrix.jsx';
import { createVoiceSocket } from '../services/voiceSocket.js';
import { apiClient } from '../services/apiClient.js';

const SpeechRecognition = typeof window !== 'undefined'
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

// How long the orb may sit idle before it hides itself. Reset on every bit of
// activity, so it never disappears while you are mid-conversation.
const IDLE_HIDE_MS = 25000;
// Gap between recognition sessions. Chrome ends the mic session on its own; we
// re-arm after a short pause so we are not restarting in a tight loop.
const RESTART_DELAY_MS = 300;
// If the backend never answers, the turn must not be left open forever - the
// orb would sit in "thinking" and never listen again. This is the watchdog.
const ANSWER_WATCHDOG_MS = 20000;

/**
 * JarvisHoloOrb - the transparent floating assistant.
 * ===========================================================================
 * VOICE LOOP
 * ----------
 * Chromium's Web Speech API ends a recognition session by itself - after a
 * period of silence, after a result, or on a network hiccup - even with
 * `continuous = true`. The documented way to keep listening is to restart the
 * recognizer from inside its own `onend` handler.
 *
 * This component previously had NO `onend` and NO `onerror`, so the mic came up
 * once, answered one question, and then stayed dead for the rest of the app's
 * life. That is the "it replies once and then stops" bug.
 *
 * The loop is now explicit and turn-based:
 *
 *     listen  ->  final transcript  ->  stop mic  ->  think  ->  speak
 *        ^                                                          |
 *        +------------------- resume listening ---------------------+
 *
 * The mic is deliberately PAUSED while Jarvis speaks, so it cannot transcribe
 * its own voice and send that back as a question.
 */
export default function JarvisHoloOrb() {
  const [orbState, setOrbState] = useState('listening'); // listening | thinking | speaking | idle | blocked
  const [transcript, setTranscript] = useState('');
  const [replyText, setReplyText] = useState('Listening, Sir...');

  const socketRef = useRef(null);
  const recognitionRef = useRef(null);
  const mountedRef = useRef(true);

  // Control flags held in refs: the recognizer callbacks are created once, so
  // they must read live values rather than closed-over state.
  const wantMicRef = useRef(true);      // do we WANT to be listening
  const speakingRef = useRef(false);    // are we currently speaking
  const restartTimerRef = useRef(null);
  const idleTimerRef = useRef(null);
  const errorStreakRef = useRef(0);
  const awaitingAnswerRef = useRef(false);   // turn handed to the backend
  const watchdogRef = useRef(null);

  const audioLevel = 0.5;

  /* ------------------------------------------------------------- idle hide */
  const armIdleHide = useCallback(() => {
    clearTimeout(idleTimerRef.current);
    idleTimerRef.current = setTimeout(() => {
      // Never hide mid-turn.
      if (speakingRef.current) return;
      window.secondBrain?.hideOrb?.();
    }, IDLE_HIDE_MS);
  }, []);

  const cancelIdleHide = useCallback(() => {
    clearTimeout(idleTimerRef.current);
  }, []);

  /* -------------------------------------------------- recognition control */
  const startMic = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec || !wantMicRef.current) return;
    if (speakingRef.current) return;   // never listen to our own voice

    try {
      rec.start();
    } catch {
      // InvalidStateError simply means it is already running - harmless.
    }
  }, []);

  /**
   * Close the current turn and start listening again.
   *
   * Every path that ends a turn goes through here - a spoken answer, a TTS
   * failure, a socket drop, or the watchdog - so there is exactly one place
   * that can leave the orb deaf, and it always re-arms.
   */
  const endTurn = useCallback(({ speakState = 'listening' } = {}) => {
    clearTimeout(watchdogRef.current);
    awaitingAnswerRef.current = false;
    speakingRef.current = false;
    if (!mountedRef.current) return;
    setOrbState(speakState);
    startMic();
    armIdleHide();
  }, [armIdleHide, startMic]);

  const stopMic = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // already stopped
    }
  }, []);

  /* -------------------------------------------------------------- speaking */
  const speakSpeech = useCallback((text) => {
    if (!text || !window.speechSynthesis) {
      speakingRef.current = false;
      startMic();
      return;
    }

    // Pause the mic for the duration of playback.
    speakingRef.current = true;
    cancelIdleHide();
    stopMic();
    setOrbState('speaking');

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const natural = voices.find(
      (v) => v.lang?.includes('en-GB') || v.name?.includes('Natural') || v.name?.includes('George')
    );
    if (natural) utterance.voice = natural;

    // `onend` is NOT guaranteed. Electron can drop the event entirely when the
    // window is hidden or the voice engine hiccups - and without it the orb
    // stays muted forever, which looks exactly like "it stopped working".
    // The bound is roughly the time the sentence needs, plus generous slack.
    let finished = false;
    const resume = () => {
      if (finished) return;   // idempotent: onend may also fire after the watchdog
      finished = true;
      clearTimeout(ttsWatchdog);
      endTurn();
    };

    const words = String(text).split(/\s+/).filter(Boolean).length;
    const ttsWatchdog = setTimeout(resume, Math.max(4000, words * 420 + 3000));

    utterance.onend = resume;
    utterance.onerror = resume;   // a failed TTS must not strand the mic

    window.speechSynthesis.speak(utterance);
  }, [armIdleHide, cancelIdleHide, endTurn, startMic, stopMic]);

  /* ----------------------------------------------------------------- init */
  useEffect(() => {
    mountedRef.current = true;
    let active = true;

    async function initOrbVoice() {
      try {
        if (!apiClient.getToken()) {
          await apiClient.login('Immanuel', 'secondbrain');
        }

        const socket = await createVoiceSocket({
          onOpen: () => {
            socket.send(JSON.stringify({ type: 'start', mode: 'continuous', language: 'mixed' }));
          },
          onEvent: (event) => {
            if (!active || !mountedRef.current) return;

            if (event.type === 'transcript') {
              setTranscript(event.text);
              setOrbState('thinking');
            } else if (event.type === 'speaking') {
              setOrbState(event.status === 'started' ? 'speaking' : 'listening');
            } else if (event.type === 'answer') {
              awaitingAnswerRef.current = false;
              clearTimeout(watchdogRef.current);
              setReplyText(event.text);
              speakSpeech(event.text);
            } else if (event.type === 'error') {
              // Backend reported a problem - release the turn instead of hanging.
              awaitingAnswerRef.current = false;
              setReplyText(event.text || 'Something went wrong. Still listening.');
              endTurn();
            }
          },
          onClose: () => {
            // The socket dropping mid-turn would otherwise leave a deaf orb.
            if (active && mountedRef.current) {
              setReplyText('Connection lost - press Alt+J to try again.');
              endTurn({ speakState: 'idle' });
            }
          }
        });
        socketRef.current = socket;
      } catch (err) {
        console.warn('Orb voice socket error:', err);
      }
    }

    initOrbVoice();

    /* ------------------------------------------------------ recognizer */
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;

      rec.onstart = () => {
        errorStreakRef.current = 0;
        if (!speakingRef.current) setOrbState('listening');
      };

      rec.onresult = (e) => {
        let interim = '';
        for (let i = e.resultIndex; i < e.results.length; i += 1) {
          const text = e.results[i][0].transcript;
          if (e.results[i].isFinal) {
            const clean = text.trim();
            if (!clean) continue;

            setTranscript(clean);
            setOrbState('thinking');
            cancelIdleHide();
            socketRef.current?.send(JSON.stringify({ type: 'transcript', text: clean, final: true }));

            // Hand the turn over to the backend: stop listening so Jarvis is
            // not recording its own reply.
            speakingRef.current = true;
            awaitingAnswerRef.current = true;
            stopMic();

            // Watchdog: if no answer arrives, resume listening rather than
            // waiting forever in "thinking".
            clearTimeout(watchdogRef.current);
            watchdogRef.current = setTimeout(() => {
              if (!awaitingAnswerRef.current) return;
              setReplyText('No answer came back - still listening.');
              endTurn();
            }, ANSWER_WATCHDOG_MS);
          } else {
            interim += text;
          }
        }
        if (interim) {
          setTranscript(interim);
          cancelIdleHide();
        }
      };

      /**
       * THE FIX. Chromium ends the session on its own; without restarting here
       * the microphone never comes back after the first question.
       */
      rec.onend = () => {
        if (!active || !mountedRef.current) return;
        if (!wantMicRef.current || speakingRef.current) return;

        clearTimeout(restartTimerRef.current);
        // Back off if the engine keeps failing, so a broken mic cannot spin.
        const delay = Math.min(RESTART_DELAY_MS * (errorStreakRef.current + 1), 4000);
        restartTimerRef.current = setTimeout(startMic, delay);
      };

      rec.onerror = (event) => {
        const code = event?.error || 'unknown';

        if (code === 'not-allowed' || code === 'service-not-allowed') {
          // Permanent failure - stop trying and say so instead of looping.
          wantMicRef.current = false;
          setOrbState('blocked');
          setReplyText(
            'Microphone blocked. Allow mic access for Jarvis in Windows Settings > Privacy, then press Alt+J again.'
          );
          return;
        }

        if (code === 'no-speech' || code === 'aborted') {
          // Normal: silence. `onend` re-arms; do not treat it as a failure.
          return;
        }

        errorStreakRef.current += 1;
        if (errorStreakRef.current === 3) {
          setReplyText('Voice input is struggling. Still listening…');
        }
      };

      recognitionRef.current = rec;
      startMic();
      armIdleHide();
    } else {
      setOrbState('blocked');
      setReplyText('Speech recognition is not available in this build.');
    }

    /* ------------------------------------------------------ wake trigger */
    const ipc = window.secondBrain;
    const unsubscribe = ipc?.onWakeTrigger?.(() => {
      // Alt+J: re-arm everything. Previously this only spoke a greeting, so a
      // dead recognizer stayed dead no matter how many times you summoned it.
      wantMicRef.current = true;
      errorStreakRef.current = 0;
      speakingRef.current = false;
      awaitingAnswerRef.current = false;
      clearTimeout(watchdogRef.current);
      cancelIdleHide();
      setOrbState('listening');
      setReplyText('Yes, Sir? How can I assist you?');

      // Re-arm the mic FIRST, then greet - otherwise the greeting is spoken
      // over a dead microphone and the greeting itself gets recorded.
      setTimeout(() => {
        startMic();
        speakSpeech('Yes, Sir? How can I assist you?');
      }, 120);
    });

    return () => {
      active = false;
      mountedRef.current = false;
      clearTimeout(restartTimerRef.current);
      clearTimeout(idleTimerRef.current);
      clearTimeout(watchdogRef.current);
      socketRef.current?.close();
      try {
        recognitionRef.current?.abort?.();
      } catch {
        // ignore
      }
      if (typeof unsubscribe === 'function') unsubscribe();
    };
  }, [armIdleHide, cancelIdleHide, endTurn, speakSpeech, startMic, stopMic]);

  /* --------------------------------------------------------------- chrome */
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

  function dismissOrb() {
    window.speechSynthesis?.cancel();
    window.secondBrain?.hideOrb?.() ?? window.close();
  }

  function openFullApp() {
    window.secondBrain?.showMain?.();
    dismissOrb();
  }

  const stateLabel = {
    listening: 'listening',
    thinking: 'thinking',
    speaking: 'speaking',
    blocked: 'mic blocked',
    idle: 'idle'
  }[orbState] || orbState;

  return (
    <div className="relative flex h-screen w-screen flex-col items-center justify-between p-2 bg-transparent select-none overflow-hidden">
      {/* Drag handle + controls */}
      <div
        style={{ WebkitAppRegion: 'drag' }}
        className="flex w-full items-center justify-between px-2 pt-1 cursor-grab active:cursor-grabbing opacity-75 hover:opacity-100 transition"
      >
        <div className="flex items-center gap-1.5 rounded-full bg-black/40 px-2.5 py-0.5 border border-amber-400/30 backdrop-blur-md">
          <span className={`flex h-1.5 w-1.5 rounded-full animate-ping ${
            orbState === 'blocked' ? 'bg-red-400' : 'bg-amber-400'
          }`} />
          <span className="text-[9px] font-bold tracking-widest text-amber-300 font-mono uppercase">
            JARVIS
          </span>
        </div>

        <div style={{ WebkitAppRegion: 'no-drag' }} className="flex items-center gap-1.5">
          {orbState === 'blocked' && <MicOff size={11} className="text-red-400" />}
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
            title="Dismiss (Alt+J to bring back)"
          >
            <X size={12} />
          </button>
        </div>
      </div>

      {/* Holographic core */}
      <div className="relative flex flex-1 items-center justify-center my-auto">
        <GoldenJarvisMatrix state={orbState} audioLevel={audioLevel} size={320} />
      </div>

      {/* Subtitle capsule */}
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
            <span>● {stateLabel}</span>
            <span>·</span>
            <span>RTX 3050 Memory Core</span>
          </div>
        </div>
      </div>
    </div>
  );
}
