import { useEffect, useState } from 'react';
import { Volume2, VolumeX, Sparkles, Play, Pause, Compass, CheckCircle2, RefreshCw } from 'lucide-react';
import { useBackend } from '../context/BackendContext.jsx';

export default function ExecutiveBriefingWidget() {
  const { apiClient } = useBackend();
  const [briefing, setBriefing] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  async function loadBriefing() {
    setIsLoading(true);
    try {
      const res = await fetch(`${apiClient.baseUrl}/api/graph/briefing/today`);
      if (res.ok) {
        const data = await res.json();
        setBriefing(data);
      }
    } catch (e) {
      console.warn('Could not load executive briefing:', e);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadBriefing();
  }, []);

  function toggleAudioBriefing() {
    if (!window.speechSynthesis || !briefing?.spoken_script) return;

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(briefing.spoken_script);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      // Select natural English voice if available
      const voices = window.speechSynthesis.getVoices();
      const britishOrNatural = voices.find(v => v.lang.includes('en-GB') || v.name.includes('Natural') || v.name.includes('George'));
      if (britishOrNatural) utterance.voice = britishOrNatural;

      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);

      window.speechSynthesis.speak(utterance);
      setIsPlaying(true);
    }
  }

  if (isLoading && !briefing) {
    return (
      <div className="glass-panel flex min-h-[140px] items-center justify-center rounded-2xl p-6">
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <RefreshCw size={15} className="animate-spin text-cyanGlow" />
          <span>Synthesizing Daily Intelligence Briefing...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-cyanGlow/25 bg-gradient-to-r from-slate-950/90 via-[#0a0f24]/90 to-slate-950/90 p-5 shadow-2xl backdrop-blur-xl">
      <div className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-cyanGlow/10 blur-3xl" />

      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        {/* Left: Briefing Overview & Voice Player */}
        <div className="max-w-2xl space-y-2">
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full border border-cyanGlow/30 bg-cyanGlow/10 px-2.5 py-0.5 text-[10px] font-bold text-cyanGlow uppercase tracking-wider">
              <Sparkles size={11} /> Executive Daily Briefing
            </span>
            <span className="text-xs font-semibold text-slate-400">{briefing?.date}</span>
          </div>

          <p className="text-sm italic leading-relaxed text-slate-200">
            "{briefing?.spoken_script || 'All cognitive telemetry synchronized. Memory vault online.'}"
          </p>

          <div className="flex items-center gap-3 pt-1">
            <button
              type="button"
              onClick={toggleAudioBriefing}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition shadow-glow ${
                isPlaying
                  ? 'border border-mintGlow/40 bg-mintGlow text-slate-950'
                  : 'border border-cyanGlow/30 bg-cyanGlow/15 text-cyanGlow hover:bg-cyanGlow/25'
              }`}
            >
              {isPlaying ? <Pause size={14} /> : <Play size={14} />}
              {isPlaying ? 'Pause Jarvis Audio' : 'Play Spoken Briefing'}
            </button>

            <span className="text-[11px] text-slate-400">
              Focus: <strong className="text-white">{briefing?.primary_focus || 'Deep Research'}</strong>
            </span>
          </div>
        </div>

        {/* Right: Key Proactive Priorities */}
        <div className="min-w-[280px] rounded-xl border border-white/5 bg-black/40 p-3.5 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <span className="flex items-center gap-1.5 text-mintGlow">
              <Compass size={13} /> Today's Trajectory
            </span>
            <span className="text-[10px] text-slate-500 font-mono">3 Objectives</span>
          </div>

          <div className="space-y-1.5">
            {(briefing?.key_priorities || [
              'Synthesize quantum and deep learning notes',
              'Inspect autonomous wiki compilations',
              'Review proactive knowledge collisions'
            ]).map((pri, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                <CheckCircle2 size={13} className="mt-0.5 shrink-0 text-cyanGlow" />
                <span className="line-clamp-1">{pri}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
