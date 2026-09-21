// Stark Industries Procedural Web Audio Synthesizer
// Generates high-tech futuristic sound cues using Web Audio API oscillators (0MB external audio assets)

class JarvisAudioSynthesizer {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
  }

  _getAudioContext() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return this.ctx;
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    return this.isMuted;
  }

  // 1. Wake Chime (Rising futuristic harmonic chime when Jarvis wakes up)
  playWakeChime() {
    if (this.isMuted) return;
    const ctx = this._getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const freqs = [380, 570, 760, 1140]; // Harmonic series

    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq * 0.8, now + idx * 0.05);
      osc.frequency.exponentialRampToValueAtTime(freq, now + idx * 0.05 + 0.1);

      gain.gain.setValueAtTime(0.001, now + idx * 0.05);
      gain.gain.linearRampToValueAtTime(0.07, now + idx * 0.05 + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.05 + 0.35);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + idx * 0.05);
      osc.stop(now + idx * 0.05 + 0.4);
    });
  }

  // 2. Synaptic Thought Blip (Subtle computing data chirp during inference)
  playThoughtBlip() {
    if (this.isMuted) return;
    const ctx = this._getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(840, now);
    osc.frequency.exponentialRampToValueAtTime(1420, now + 0.06);

    gain.gain.setValueAtTime(0.03, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.08);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.09);
  }

  // 3. Cognitive Collision Alert (Futuristic radar pulse when proactive insight found)
  playInsightAlert() {
    if (this.isMuted) return;
    const ctx = this._getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const freqs = [520, 650];

    freqs.forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now + i * 0.09);

      gain.gain.setValueAtTime(0.001, now + i * 0.09);
      gain.gain.linearRampToValueAtTime(0.09, now + i * 0.09 + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.09 + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now + i * 0.09);
      osc.stop(now + i * 0.09 + 0.32);
    });
  }

  // 4. Synthesis Complete (Soft golden resolution chord)
  playSuccessChime() {
    if (this.isMuted) return;
    const ctx = this._getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const freqs = [440, 554.37, 659.25, 880]; // A Major triad

    freqs.forEach((freq) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.06, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.6);
    });
  }
}

export const soundEffects = new JarvisAudioSynthesizer();
