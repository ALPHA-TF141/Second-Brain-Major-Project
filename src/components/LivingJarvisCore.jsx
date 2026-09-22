import { useEffect, useRef } from 'react';

export default function LivingJarvisCore({
  state = 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking'
  audioLevel = 0.5,
  onClick = null
}) {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    // Canvas 2D can be unavailable (missing/blacklisted GPU, software rendering
    // disabled, headless contexts). Bail out cleanly instead of crashing the
    // whole React tree into the red JARVIS diagnostic screen.
    if (!ctx) return undefined;
    let animationFrameId;

    // 1. Generate 3D Spherical Particle Core
    const PARTICLE_COUNT = 480;
    const particles = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      const radius = 140 + (Math.random() - 0.5) * 35;

      particles.push({
        origX: radius * Math.sin(phi) * Math.cos(theta),
        origY: radius * Math.sin(phi) * Math.sin(theta),
        origZ: radius * Math.cos(phi),
        baseSize: Math.random() * 2.5 + 1.0,
        speed: (Math.random() - 0.5) * 0.015,
        pulseOffset: Math.random() * Math.PI * 2,
        isSpark: Math.random() > 0.85
      });
    }

    let time = 0;

    const render = () => {
      time += 0.02;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      const fov = 480;

      // Smooth mouse tracking (makes the AI look at user's cursor!)
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

      const isListening = state === 'listening';
      const isThinking = state === 'thinking';
      const isSpeaking = state === 'speaking';

      // State Energy Modifiers
      const energy = isListening
        ? 1.0 + audioLevel * 2.0
        : isThinking
        ? 2.2
        : isSpeaking
        ? 1.5 + Math.sin(time * 6) * 0.3
        : 1.0 + Math.sin(time * 2) * 0.12;

      // Dynamic Color Scheme (Gold when speaking/thinking, Cyan when idle/listening)
      const isGoldTheme = isSpeaking || isThinking;
      const primaryColor = isGoldTheme ? '#fbbf24' : '#38bdf8';
      const sparkColor = isGoldTheme ? '#ffffff' : '#e0f2fe';

      const rotY = time * 0.35 * (isThinking ? 2.0 : 1.0) + mouseRef.current.x * 0.4;
      const rotX = Math.sin(time * 0.3) * 0.15 + mouseRef.current.y * 0.3;

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      // ================= 1. CENTRAL SINGULARITY ARC-REACTOR CORE =================
      const coreR = (48 + Math.sin(time * 3.5) * 6) * energy;
      const coreGrad = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, coreR * 2.4);
      if (isGoldTheme) {
        coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
        coreGrad.addColorStop(0.2, 'rgba(251, 191, 36, 0.85)');
        coreGrad.addColorStop(0.55, 'rgba(217, 119, 6, 0.35)');
        coreGrad.addColorStop(0.85, 'rgba(180, 83, 9, 0.08)');
        coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      } else {
        coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
        coreGrad.addColorStop(0.25, 'rgba(56, 189, 248, 0.85)');
        coreGrad.addColorStop(0.6, 'rgba(2, 132, 199, 0.3)');
        coreGrad.addColorStop(0.9, 'rgba(3, 105, 161, 0.06)');
        coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      }

      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreR * 2.4, 0, Math.PI * 2);
      ctx.fill();

      // ================= 2. 3D GYROSCOPIC HOLOGRAPHIC TELEMETRY RINGS =================
      const rings = [
        { r: 160, pitch: 0.1, roll: time * 0.25, dashes: [24, 8, 4, 8], w: 1.8, alpha: 0.8 },
        { r: 185, pitch: 1.15, roll: -time * 0.3, dashes: [6, 6], w: 1.2, alpha: 0.65 },
        { r: 215, pitch: -0.75, roll: time * 0.18, dashes: [45, 12, 6, 12], w: 2.2, alpha: 0.9 },
        { r: 135, pitch: 0.6, roll: time * 0.55, dashes: [], w: 1.0, alpha: 0.5 },
        { r: 240, pitch: -1.35, roll: -time * 0.12, dashes: [3, 12], w: 1.0, alpha: 0.45 }
      ];

      for (let idx = 0; idx < rings.length; idx++) {
        const ring = rings[idx];
        const rRadius = ring.r * (1.0 + Math.sin(time * 3 + idx) * 0.03 * energy);

        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(ring.roll);
        ctx.scale(1, Math.cos(ring.pitch + rotX));

        ctx.lineWidth = ring.w;
        ctx.strokeStyle = isGoldTheme
          ? `rgba(251, 191, 36, ${ring.alpha})`
          : `rgba(56, 189, 248, ${ring.alpha})`;
        ctx.setLineDash(ring.dashes);
        ctx.shadowColor = primaryColor;
        ctx.shadowBlur = isThinking ? 20 : 10;

        ctx.beginPath();
        ctx.arc(0, 0, rRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Orbiting Telemetry Data Nodes
        const nodeAngle = time * (idx % 2 === 0 ? 1 : -1) * (0.9 + idx * 0.15);
        const nx = Math.cos(nodeAngle) * rRadius;
        const ny = Math.sin(nodeAngle) * rRadius;

        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ffffff';
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.arc(nx, ny, 3.2, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }

      // ================= 3. 3D PARTICLE NEURAL SPHERE =================
      const projected = [];
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        const pTheta = time * p.speed + p.pulseOffset;
        const pPulse = Math.sin(pTheta) * 0.08 * energy;

        const currX = p.origX * (1 + pPulse);
        const currY = p.origY * (1 + pPulse);
        const currZ = p.origZ * (1 + pPulse);

        const x1 = currX * cosY - currZ * sinY;
        const z1 = currZ * cosY + currX * sinY;
        const y2 = currY * cosX - z1 * sinX;
        const z2 = z1 * cosX + currY * sinX;

        const scale = fov / (fov + z2 + 280);
        const projX = centerX + x1 * scale;
        const projY = centerY + y2 * scale;

        projected.push({
          x: projX,
          y: projY,
          z: z2,
          scale,
          baseSize: p.baseSize,
          isSpark: p.isSpark || (i + Math.floor(time * 12)) % 22 === 0
        });
      }

      // Depth sorting
      projected.sort((a, b) => b.z - a.z);

      // Draw Particles with Luminous Perspective Glow
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        const radius = Math.max(0.8, p.baseSize * p.scale);
        const depthRatio = Math.max(0.18, (p.z + 180) / 360);

        if (p.isSpark) {
          ctx.fillStyle = sparkColor;
          ctx.shadowColor = '#ffffff';
          ctx.shadowBlur = 16;
        } else {
          ctx.fillStyle = isGoldTheme
            ? `rgba(251, 191, 36, ${depthRatio * 0.9})`
            : `rgba(56, 189, 248, ${depthRatio * 0.9})`;
          ctx.shadowColor = primaryColor;
          ctx.shadowBlur = isListening ? 10 : 5;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.shadowBlur = 0;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    // Mouse Tracking (Subtle interactive gaze)
    const onMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      mouseRef.current.targetX = nx;
      mouseRef.current.targetY = ny;
    };

    window.addEventListener('mousemove', onMouseMove);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', onMouseMove);
    };
  }, [state, audioLevel]);

  return (
    <div
      onClick={onClick}
      className="relative flex h-full w-full cursor-pointer items-center justify-center select-none"
    >
      <canvas ref={canvasRef} className="h-full w-full max-w-[620px] max-h-[620px]" />
    </div>
  );
}
