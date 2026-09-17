import { useEffect, useRef, useState } from 'react';
import { Cpu, Eye, Sparkles, Zap, Activity } from 'lucide-react';

export default function NeuralBrain3D({
  state = 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking'
  energy = 1.0,
  domainFocus = 'Technology & Science',
  nodeCount = 450,
  onNodeAdded = null
}) {
  const canvasRef = useRef(null);
  const [synapseCount, setSynapseCount] = useState(nodeCount);
  const [recentBirth, setRecentBirth] = useState(null);
  const rotationRef = useRef({ x: 0.18, y: 0.0, vx: 0, vy: 0.006 });
  const isDraggingRef = useRef(false);
  const lastMouseRef = useRef({ x: 0, y: 0 });
  const birthWavesRef = useRef([]);

  // Trigger Synaptic Burst when new nodeCount arrives
  useEffect(() => {
    if (nodeCount > synapseCount) {
      const added = nodeCount - synapseCount;
      setSynapseCount(nodeCount);
      setRecentBirth(`+${added} Synaptic Nodes Formed`);

      // Trigger outward shockwave ripples in 3D
      birthWavesRef.current.push({
        radius: 10,
        maxRadius: 180,
        opacity: 1.0,
        color: '#f6d365'
      });

      const timer = setTimeout(() => setRecentBirth(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [nodeCount, synapseCount]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    // Generate 3D Brain Point Cloud (Dual Hemisphere Architecture)
    const points = [];
    const POINT_COUNT = 520;

    for (let i = 0; i < POINT_COUNT; i++) {
      const hemisphere = i % 2 === 0 ? -1 : 1;
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = Math.cbrt(Math.random()) * 0.92 + 0.08;

      let x = r * Math.sin(phi) * Math.cos(theta) * 0.85;
      let y = r * Math.cos(phi) * 0.68;
      let z = r * Math.sin(phi) * Math.sin(theta) * 1.15;

      // Medial sagittal fissure separation
      x = x + hemisphere * 0.38;

      // Frontal & occipital curvature
      if (z > 0.3) y += 0.14;
      if (z < -0.35) y -= 0.18;

      points.push({
        origX: x * 165,
        origY: y * 165,
        origZ: z * 165,
        baseSize: Math.random() * 2.4 + 1.2,
        hemisphere,
        pulseOffset: Math.random() * Math.PI * 2,
        connections: [],
        sparkTime: Math.random() * 100
      });
    }

    // Connect nearest nodes with synaptic lines
    for (let i = 0; i < points.length; i++) {
      const nearest = [];
      for (let j = i + 1; j < points.length; j++) {
        const dx = points[i].origX - points[j].origX;
        const dy = points[i].origY - points[j].origY;
        const dz = points[i].origZ - points[j].origZ;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < 42 && points[i].hemisphere === points[j].hemisphere) {
          nearest.push({ target: j, dist });
        }
      }
      points[i].connections = nearest.slice(0, 3);
    }

    let time = 0;

    const render = () => {
      time += 0.025;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      const fov = 460;

      // Inertial auto-rotation
      if (!isDraggingRef.current) {
        const baseSpeed = state === 'listening' ? 0.012 : state === 'thinking' ? 0.02 : 0.007;
        rotationRef.current.y += baseSpeed;
        rotationRef.current.x = Math.sin(time * 0.35) * 0.08 + 0.15;
      }

      const rotX = rotationRef.current.x;
      const rotY = rotationRef.current.y;
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);

      // 1. Draw Holographic Gyro Orbital Rings
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.12)';
      ctx.beginPath();
      ctx.ellipse(0, 0, 260, 95, time * 0.2, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(0, 255, 160, 0.08)';
      ctx.beginPath();
      ctx.ellipse(0, 0, 290, 110, -time * 0.15, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // 2. Project Points
      const projected = [];
      for (let i = 0; i < points.length; i++) {
        const p = points[i];

        // Synaptic pulse excitation
        let pulse = Math.sin(time * 2.8 + p.pulseOffset) * 2.2;
        if (state === 'listening' || state === 'speaking') {
          pulse *= 4.0 * energy;
        }

        const currX = p.origX + (p.origX / 165) * pulse;
        const currY = p.origY + (p.origY / 165) * pulse;
        const currZ = p.origZ + (p.origZ / 165) * pulse;

        const x1 = currX * cosY - currZ * sinY;
        const z1 = currZ * cosY + currX * sinY;
        const y2 = currY * cosX - z1 * sinX;
        const z2 = z1 * cosX + currY * sinX;

        const scale = fov / (fov + z2 + 280);
        const projX = centerX + x1 * scale;
        const projY = centerY + y2 * scale;

        // Spark calculation
        const isSpark = (i + Math.floor(time * 12)) % 28 === 0;

        projected.push({
          x: projX,
          y: projY,
          z: z2,
          scale,
          baseSize: p.baseSize,
          connections: p.connections,
          spark: isSpark
        });
      }

      // Sort by depth
      projected.sort((a, b) => b.z - a.z);

      // 3. Render Synaptic Axon Links
      ctx.lineWidth = 0.85;
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        if (p.z < -140) continue;

        for (let c = 0; c < p.connections.length; c++) {
          const target = projected[p.connections[c].target];
          if (!target) continue;

          // Color gradient based on depth
          const depthRatio = Math.max(0.15, (p.z + 180) / 360);
          if (p.spark) {
            ctx.strokeStyle = `rgba(246, 211, 101, ${depthRatio * 0.9})`;
          } else if (state === 'listening') {
            ctx.strokeStyle = `rgba(0, 245, 160, ${depthRatio * 0.45})`;
          } else {
            ctx.strokeStyle = `rgba(0, 242, 254, ${depthRatio * 0.35})`;
          }

          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(target.x, target.y);
          ctx.stroke();
        }
      }

      // 4. Render 3D Neural Nodes with Depth Glow
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        const radius = Math.max(0.9, p.baseSize * p.scale);
        const depthGlow = Math.max(0.2, (p.z + 180) / 360);

        if (p.spark) {
          ctx.fillStyle = '#f6d365';
          ctx.shadowColor = '#f6d365';
          ctx.shadowBlur = 16;
        } else if (state === 'listening') {
          ctx.fillStyle = `rgba(0, 245, 160, ${depthGlow})`;
          ctx.shadowColor = '#00f5a0';
          ctx.shadowBlur = 10;
        } else if (state === 'thinking') {
          ctx.fillStyle = `rgba(168, 85, 247, ${depthGlow})`;
          ctx.shadowColor = '#a855f7';
          ctx.shadowBlur = 12;
        } else {
          ctx.fillStyle = `rgba(0, 242, 254, ${depthGlow})`;
          ctx.shadowColor = '#00f2fe';
          ctx.shadowBlur = 6;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      // 5. Render Synaptic Birth Shockwaves (when new nodes pop up)
      for (let w = birthWavesRef.current.length - 1; w >= 0; w--) {
        const wave = birthWavesRef.current[w];
        wave.radius += 3.5;
        wave.opacity -= 0.018;

        ctx.save();
        ctx.strokeStyle = `rgba(246, 211, 101, ${wave.opacity})`;
        ctx.lineWidth = 2.5;
        ctx.shadowColor = '#f6d365';
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.arc(centerX, centerY, wave.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        if (wave.opacity <= 0) {
          birthWavesRef.current.splice(w, 1);
        }
      }

      ctx.shadowBlur = 0;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    // Mouse Controls
    const onMouseDown = (e) => {
      isDraggingRef.current = true;
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    };
    const onMouseMove = (e) => {
      if (!isDraggingRef.current) return;
      const dx = e.clientX - lastMouseRef.current.x;
      const dy = e.clientY - lastMouseRef.current.y;
      rotationRef.current.y += dx * 0.007;
      rotationRef.current.x += dy * 0.007;
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    };
    const onMouseUp = () => { isDraggingRef.current = false; };

    // Double-click to inject synthetic synaptic burst
    const onDoubleClick = () => {
      birthWavesRef.current.push({
        radius: 12,
        maxRadius: 200,
        opacity: 1.0,
        color: '#00f2fe'
      });
      setRecentBirth('⚡ Synapse Stimulation Pulse');
      setTimeout(() => setRecentBirth(null), 2500);
    };

    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('dblclick', onDoubleClick);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    return () => {
      cancelAnimationFrame(animationFrameId);
      canvas.removeEventListener('mousedown', onMouseDown);
      canvas.removeEventListener('dblclick', onDoubleClick);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [state, energy]);

  const stateBadges = {
    idle: { label: 'NEURAL CORTEX · SYNCHRONIZED', style: 'border-cyan-400/30 bg-cyan-500/10 text-cyan-300' },
    listening: { label: 'SENSORY STREAM · AUDIO INGESTION', style: 'border-emerald-400/40 bg-emerald-500/15 text-emerald-300 shadow-glow animate-pulse' },
    thinking: { label: 'COGNITIVE REASONING · INFERENCE', style: 'border-purple-400/40 bg-purple-500/15 text-purple-300 animate-pulse' },
    speaking: { label: 'NEURAL AUDIO · SYNTHESIS', style: 'border-teal-400/40 bg-teal-500/15 text-teal-300 shadow-glow' }
  };

  const badge = stateBadges[state] || stateBadges.idle;

  return (
    <div className="relative flex flex-col items-center justify-between overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-slate-950/90 via-[#070b18]/90 to-slate-950/90 p-5 shadow-2xl backdrop-blur-2xl">
      {/* Top HUD Telemetry Bar */}
      <div className="z-10 flex w-full items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow shadow-glow">
            <Cpu size={19} />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wider text-slate-100 uppercase">Jarvis Autonomous Cognitive Core</h3>
            <p className="text-xs text-slate-400">Quantum Neural Mesh · {synapseCount} Active Synaptic Nodes</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {recentBirth && (
            <span className="flex items-center gap-1.5 rounded-full border border-amber-400/50 bg-amber-500/20 px-3 py-1 text-xs font-bold text-amber-300 shadow-glow animate-bounce">
              <Zap size={13} />
              {recentBirth}
            </span>
          )}
          <span className={`rounded-full border px-3.5 py-1 text-[11px] font-bold tracking-wider uppercase ${badge.style}`}>
            {badge.label}
          </span>
        </div>
      </div>

      {/* Massive 3D Brain Viewport */}
      <div className="relative my-2 h-[380px] w-full max-w-[700px] cursor-grab active:cursor-grabbing">
        <canvas ref={canvasRef} className="h-full w-full" />
        <div className="pointer-events-none absolute bottom-2 right-4 flex items-center gap-2 rounded-lg bg-black/40 px-2.5 py-1 text-[11px] text-slate-400 backdrop-blur-md">
          <Sparkles size={12} className="text-cyanGlow" />
          <span>Click & Drag to Orbit · Double-Click to Stimulate</span>
        </div>
      </div>

      {/* Bottom Telemetry Status HUD */}
      <div className="z-10 flex w-full flex-wrap items-center justify-between gap-2 rounded-xl border border-white/5 bg-white/5 px-4 py-2.5 text-xs text-slate-300">
        <div className="flex items-center gap-2.5">
          <Eye size={15} className="text-cyanGlow" />
          <span>Priority Focus: <strong className="text-white">{domainFocus}</strong></span>
        </div>

        <div className="flex items-center gap-4 text-[11px] text-slate-400">
          <span className="flex items-center gap-1 text-mintGlow">
            <Activity size={13} /> Ephemeral Zero-Storage Active
          </span>
          <span className="font-mono text-cyanGlow/90">Autonomous GitHub Sync: 60s</span>
        </div>
      </div>
    </div>
  );
}
