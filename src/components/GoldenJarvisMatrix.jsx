import { useEffect, useRef } from 'react';

export default function GoldenJarvisMatrix({
  state = 'listening', // 'idle' | 'listening' | 'thinking' | 'speaking'
  audioLevel = 0.5,
  size = 380
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    // Canvas 2D can be unavailable (missing/blacklisted GPU, software rendering
    // disabled, headless contexts). Bail out cleanly instead of crashing the
    // whole React tree into the red JARVIS diagnostic screen.
    if (!ctx) return undefined;
    let animationFrameId;

    // Generate Golden Particle Cloud (Inner Shell & Outer Cage)
    const PARTICLE_COUNT = 320;
    const particles = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      const layer = Math.random() > 0.35 ? 135 : 95; // Dual shell
      const r = layer + (Math.random() - 0.5) * 20;

      particles.push({
        origX: r * Math.sin(phi) * Math.cos(theta),
        origY: r * Math.sin(phi) * Math.sin(theta),
        origZ: r * Math.cos(phi),
        baseSize: Math.random() * 2.2 + 0.8,
        pulseOffset: Math.random() * Math.PI * 2,
        speed: (Math.random() - 0.5) * 0.015
      });
    }

    let time = 0;

    const render = () => {
      time += 0.025;
      const width = canvas.clientWidth || size;
      const height = canvas.clientHeight || size;

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      const fov = 420;

      // Dynamics based on state
      const isListening = state === 'listening';
      const isThinking = state === 'thinking';
      const isSpeaking = state === 'speaking';

      const energyMod = isListening ? (1.0 + audioLevel * 1.5) : isThinking ? 2.0 : isSpeaking ? 1.4 : 0.8;
      const rotY = time * 0.45 * (isThinking ? 1.8 : 1.0);
      const rotX = Math.sin(time * 0.3) * 0.2 + 0.15;
      const rotZ = Math.cos(time * 0.25) * 0.15;

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      // 1. Central Golden Singularity Core (Bloom Glow)
      const coreRadius = (35 + Math.sin(time * 4) * 6) * (isSpeaking ? 1.3 : 1.0);
      const coreGrad = ctx.createRadialGradient(centerX, centerY, 2, centerX, centerY, coreRadius * 2.2);
      coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
      coreGrad.addColorStop(0.2, 'rgba(255, 224, 102, 0.85)');
      coreGrad.addColorStop(0.5, 'rgba(255, 170, 0, 0.45)');
      coreGrad.addColorStop(0.8, 'rgba(230, 115, 0, 0.15)');
      coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreRadius * 2.2, 0, Math.PI * 2);
      ctx.fill();

      // 2. Draw 3D Rotating Golden Concentric Orbital Rings (Iron Man Telemetry Style)
      const rings = [
        { radius: 140, pitch: 0.0, roll: time * 0.3, width: 1.5, dashes: [12, 6, 2, 6], color: 'rgba(255, 183, 3, 0.7)' },
        { radius: 165, pitch: 1.1, roll: -time * 0.4, width: 1.2, dashes: [4, 4], color: 'rgba(251, 133, 0, 0.65)' },
        { radius: 185, pitch: -0.75, roll: time * 0.2, width: 2.0, dashes: [30, 8, 4, 8], color: 'rgba(255, 214, 10, 0.85)' },
        { radius: 115, pitch: 0.5, roll: time * 0.6, width: 1.0, dashes: [], color: 'rgba(255, 170, 0, 0.5)' },
        { radius: 200, pitch: -1.3, roll: -time * 0.15, width: 0.8, dashes: [2, 10], color: 'rgba(255, 238, 140, 0.4)' }
      ];

      for (let r = 0; r < rings.length; r++) {
        const ring = rings[r];
        const rRadius = ring.radius * (1.0 + Math.sin(time * 3 + r) * 0.02 * energyMod);

        ctx.save();
        ctx.translate(centerX, centerY);

        // Apply 3D rotation matrix
        ctx.rotate(ring.roll);
        ctx.scale(1, Math.cos(ring.pitch + rotX));

        ctx.lineWidth = ring.width;
        ctx.strokeStyle = ring.color;
        ctx.setLineDash(ring.dashes);
        ctx.shadowColor = '#ffb703';
        ctx.shadowBlur = isThinking ? 18 : 8;

        ctx.beginPath();
        ctx.arc(0, 0, rRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Draw Telemetry Data Nodes along ring
        const nodeAngle = time * (r % 2 === 0 ? 1 : -1) * (0.8 + r * 0.2);
        const nx = Math.cos(nodeAngle) * rRadius;
        const ny = Math.sin(nodeAngle) * rRadius;

        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ffdd55';
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(nx, ny, 3.0, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }

      // 3. Project & Draw 3D Golden Particle Cloud
      const projected = [];
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Orbit rotation
        const pTheta = time * p.speed + p.pulseOffset;
        const pSin = Math.sin(pTheta) * 0.08;

        const currX = p.origX * (1 + pSin * energyMod);
        const currY = p.origY * (1 + pSin * energyMod);
        const currZ = p.origZ * (1 + pSin * energyMod);

        // 3D rotation
        const x1 = currX * cosY - currZ * sinY;
        const z1 = currZ * cosY + currX * sinY;
        const y2 = currY * cosX - z1 * sinX;
        const z2 = z1 * cosX + currY * sinX;

        const scale = fov / (fov + z2 + 250);
        const projX = centerX + x1 * scale;
        const projY = centerY + y2 * scale;

        projected.push({
          x: projX,
          y: projY,
          z: z2,
          scale,
          baseSize: p.baseSize,
          isSpark: (i + Math.floor(time * 10)) % 18 === 0
        });
      }

      // Sort by depth
      projected.sort((a, b) => b.z - a.z);

      // Draw Particle Sparks with Golden Luminescence
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        const radius = Math.max(0.7, p.baseSize * p.scale);
        const depthGlow = Math.max(0.15, (p.z + 180) / 360);

        if (p.isSpark) {
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#ffe066';
          ctx.shadowBlur = 14;
        } else {
          ctx.fillStyle = `rgba(255, 183, 3, ${depthGlow * 0.9})`;
          ctx.shadowColor = '#fb8500';
          ctx.shadowBlur = isListening ? 8 : 4;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.shadowBlur = 0;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [state, audioLevel, size]);

  return (
    <div className="relative flex items-center justify-center">
      <canvas
        ref={canvasRef}
        style={{ width: `${size}px`, height: `${size}px` }}
        className="pointer-events-none"
      />
    </div>
  );
}
