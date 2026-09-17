import { useEffect, useRef, useState } from 'react';
import { Cpu, Eye, Sparkles } from 'lucide-react';

export default function NeuralBrain3D({
  state = 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking'
  energy = 1.0,
  domainFocus = 'Technology & Science'
}) {
  const canvasRef = useRef(null);
  const [activeNodesCount, setActiveNodesCount] = useState(420);
  const rotationRef = useRef({ x: 0.2, y: 0.0 });
  const isDraggingRef = useRef(false);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    // Generate 3D Brain Point Cloud (Dual Hemisphere Structure)
    const POINT_COUNT = 450;
    const points = [];

    for (let i = 0; i < POINT_COUNT; i++) {
      // Hemisphere: -1 for left, +1 for right
      const hemisphere = i % 2 === 0 ? -1 : 1;

      // Parametric organic brain volume distribution
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = Math.cbrt(Math.random()) * 0.9 + 0.1;

      // Base ellipsoid shape
      let x = r * Math.sin(phi) * Math.cos(theta) * 0.82;
      let y = r * Math.cos(phi) * 0.65;
      let z = r * Math.sin(phi) * Math.sin(theta) * 1.1;

      // Separate into dual hemispheres with medial cleft
      x = x + hemisphere * 0.35;

      // Shape frontal and occipital lobes
      if (z > 0.3) y += 0.12; // Frontal lobe elevation
      if (z < -0.4) y -= 0.15; // Cerebellum slope

      points.push({
        origX: x * 150,
        origY: y * 150,
        origZ: z * 150,
        x: x * 150,
        y: y * 150,
        z: z * 150,
        baseSize: Math.random() * 2.2 + 1.2,
        hemisphere,
        pulseOffset: Math.random() * Math.PI * 2,
        connections: []
      });
    }

    // Connect nearby nodes with synaptic links
    for (let i = 0; i < points.length; i++) {
      const nearest = [];
      for (let j = i + 1; j < points.length; j++) {
        const dx = points[i].origX - points[j].origX;
        const dy = points[i].origY - points[j].origY;
        const dz = points[i].origZ - points[j].origZ;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < 36 && points[i].hemisphere === points[j].hemisphere) {
          nearest.push({ target: j, dist });
        }
      }
      points[i].connections = nearest.slice(0, 3);
    }

    // Dynamic state palette
    const stateColors = {
      idle: { core: '#00f2fe', glow: 'rgba(0, 242, 254, 0.4)', spark: '#4facfe', speed: 0.007 },
      listening: { core: '#00f5a0', glow: 'rgba(0, 245, 160, 0.7)', spark: '#00d9f5', speed: 0.015 },
      thinking: { core: '#a18cd1', glow: 'rgba(251, 194, 235, 0.8)', spark: '#f6d365', speed: 0.025 },
      speaking: { core: '#38ef7d', glow: 'rgba(17, 153, 142, 0.65)', spark: '#11998e', speed: 0.012 }
    };

    let time = 0;

    const render = () => {
      time += 0.03;
      const theme = stateColors[state] || stateColors.idle;

      // Handle canvas resize
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2 + 10;
      const fov = 400;

      // Auto rotation when not dragging
      if (!isDraggingRef.current) {
        rotationRef.current.y += theme.speed;
        rotationRef.current.x = Math.sin(time * 0.4) * 0.08 + 0.15;
      }

      const rotX = rotationRef.current.x;
      const rotY = rotationRef.current.y;

      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);

      // Project 3D points
      const projected = [];
      for (let i = 0; i < points.length; i++) {
        const p = points[i];

        // Synaptic vibration / energy pulse
        let pulse = Math.sin(time * 3 + p.pulseOffset) * 2;
        if (state === 'listening' || state === 'speaking') {
          pulse *= 3.5 * energy;
        }

        const currX = p.origX + (p.origX / 150) * pulse;
        const currY = p.origY + (p.origY / 150) * pulse;
        const currZ = p.origZ + (p.origZ / 150) * pulse;

        // Rotate Y
        const x1 = currX * cosY - currZ * sinY;
        const z1 = currZ * cosY + currX * sinY;

        // Rotate X
        const y2 = currY * cosX - z1 * sinX;
        const z2 = z1 * cosX + currY * sinX;

        // Depth perspective projection
        const scale = fov / (fov + z2 + 250);
        const projX = centerX + x1 * scale;
        const projY = centerY + y2 * scale;

        projected.push({
          x: projX,
          y: projY,
          z: z2,
          scale,
          baseSize: p.baseSize,
          connections: p.connections,
          spark: (i + Math.floor(time * 8)) % 25 === 0
        });
      }

      // Sort by depth (back to front)
      projected.sort((a, b) => b.z - a.z);

      // 1. Draw Synaptic Links
      ctx.lineWidth = 0.75;
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        if (p.z < -100) continue; // Don't draw far back lines

        for (let c = 0; c < p.connections.length; c++) {
          const target = projected[p.connections[c].target];
          if (!target) continue;

          ctx.strokeStyle = p.spark ? theme.spark : theme.glow;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(target.x, target.y);
          ctx.stroke();
        }
      }

      // 2. Draw Neural Nodes (Particles)
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        const radius = Math.max(0.8, p.baseSize * p.scale);

        // Outer glow
        ctx.fillStyle = p.spark ? theme.spark : theme.core;
        ctx.shadowColor = p.spark ? theme.spark : theme.core;
        ctx.shadowBlur = p.spark ? 14 : (state === 'thinking' ? 10 : 5);

        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.shadowBlur = 0; // Reset shadow for next frame
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    // Mouse drag handlers for full 3D interactive rotation
    const onMouseDown = (e) => {
      isDraggingRef.current = true;
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    };
    const onMouseMove = (e) => {
      if (!isDraggingRef.current) return;
      const dx = e.clientX - lastMouseRef.current.x;
      const dy = e.clientY - lastMouseRef.current.y;
      rotationRef.current.y += dx * 0.008;
      rotationRef.current.x += dy * 0.008;
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
    };
    const onMouseUp = () => { isDraggingRef.current = false; };

    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    return () => {
      cancelAnimationFrame(animationFrameId);
      canvas.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [state, energy]);

  const stateBadges = {
    idle: { label: 'COGNITIVE CORE · IDLE', style: 'border-cyan-400/30 bg-cyan-500/10 text-cyan-300' },
    listening: { label: 'SYNAPTIC SENSORS · LISTENING', style: 'border-emerald-400/40 bg-emerald-500/15 text-emerald-300 shadow-glow' },
    thinking: { label: 'AGENTIC REASONING · INFERENCE', style: 'border-purple-400/40 bg-purple-500/15 text-purple-300 animate-pulse' },
    speaking: { label: 'NEURAL AUDIO · SYNTHESIS', style: 'border-teal-400/40 bg-teal-500/15 text-teal-300 shadow-glow' }
  };

  const badge = stateBadges[state] || stateBadges.idle;

  return (
    <div className="relative flex flex-col items-center justify-center overflow-hidden rounded-xl border border-white/10 bg-slate-950/70 p-4 shadow-2xl backdrop-blur-md">
      {/* Top HUD Status Header */}
      <div className="z-10 flex w-full items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 text-cyanGlow">
            <Cpu size={16} />
          </div>
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-300">Jarvis Neural Cortex</h4>
            <p className="text-[10px] text-slate-500">Live 3D Cognitive Lattice · {activeNodesCount} Synapses</p>
          </div>
        </div>
        <span className={`rounded-full border px-3 py-0.5 text-[10px] font-bold tracking-wide uppercase ${badge.style}`}>
          {badge.label}
        </span>
      </div>

      {/* 3D Brain Canvas */}
      <div className="relative my-2 h-72 w-full max-w-[500px] cursor-grab active:cursor-grabbing">
        <canvas ref={canvasRef} className="h-full w-full" />
        <div className="pointer-events-none absolute bottom-1 right-2 flex items-center gap-1.5 text-[10px] text-slate-500">
          <Sparkles size={11} className="text-cyanGlow" />
          <span>Drag to orbit 3D cortex</span>
        </div>
      </div>

      {/* Real-time Domain Focus Banner */}
      <div className="z-10 flex w-full items-center justify-between rounded-lg border border-white/5 bg-white/5 px-3 py-2 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <Eye size={14} className="text-cyanGlow" />
          <span>Priority Focus: <strong className="text-slate-200">{domainFocus}</strong></span>
        </div>
        <span className="text-[10px] text-mintGlow">Ephemeral OCR Active · 0MB Local Bloat</span>
      </div>
    </div>
  );
}
