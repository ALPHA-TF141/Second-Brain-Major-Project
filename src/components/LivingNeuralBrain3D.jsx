import { useEffect, useRef, useState } from 'react';

/**
 * LivingNeuralBrain3D
 * ---------------------------------------------------------------------------
 * A breathtaking, high-fidelity 3D Living Neural Brain simulation.
 * Features:
 *  - Mathematically modeled 3D dual-hemisphere cerebral cortex + brainstem
 *  - Synaptic connections (axons) with dynamic traveling electrical action potentials
 *  - 3D mouse rotation (drag to orbit 360°, mouse gaze tracking)
 *  - Reactive AI consciousness states:
 *      * 'idle' / 'awake' -> Azure & cyan tranquil synaptic respiration
 *      * 'chatting'       -> Dual cyan & warm amber conversational firings
 *      * 'agent'          -> Cybernetic emerald & electric gold autonomous pulses
 *      * 'research'       -> Ultraviolet & deep indigo quantum hyper-search waves
 *      * 'speaking'       -> Audio-reactive amplitude bursts with holographic rings
 *  - Interactive cognitive nodes with holographic telemetry labels
 */
export default function LivingNeuralBrain3D({
  mode = 'idle', // 'idle' | 'chatting' | 'agent' | 'research' | 'speaking'
  audioLevel = 0.5,
  onNodeClick = null,
  activeTrait = 'agent'
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  // 3D Orbit & Mouse tracking refs
  const rotRef = useRef({ x: 0.15, y: 0.0, targetX: 0.15, targetY: 0.0 });
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });
  const mouseGazeRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId;
    let time = 0;

    // --- 1. GENERATE 3D ANATOMICAL NEURAL BRAIN NODES ---
    // Two hemispheres: left (x < 0) and right (x > 0), separated by a longitudinal fissure.
    const NODE_COUNT = 520;
    const nodes = [];

    // Major Cognitive Nuclei with special tags
    const HUB_INDICES = [12, 45, 98, 160, 240, 310];
    const HUB_LABELS = {
      12: { title: 'Executive Prefrontal Cortex', desc: 'Autonomous Task Planning' },
      45: { title: 'Temporal Memory Vault', desc: 'Obsidian & Hybrid Graph RAG' },
      98: { title: 'Wernicke Speech Synthesizer', desc: 'Real-time Conversational AI' },
      160: { title: 'Deep Research Center', desc: 'Multi-source Knowledge Synthesis' },
      240: { title: 'Connected Apps Nexus', desc: 'Gmail, Calendar & Live APIs' },
      310: { title: 'Local Qwen 2.5 Core', desc: 'RTX 3050 Tensor Inference' }
    };

    for (let i = 0; i < NODE_COUNT; i++) {
      // Determine hemisphere: half left, half right
      const isRight = i % 2 === 0;
      const hemiSign = isRight ? 1 : -1;

      // Brain parametric coordinates
      const u = Math.random() * Math.PI; // 0 to PI
      const v = Math.random() * 2 * Math.PI; // 0 to 2PI

      // Ellipsoidal brain proportions: X (width), Y (height), Z (depth)
      const baseRadiusX = 135;
      const baseRadiusY = 110;
      const baseRadiusZ = 160;

      // Cortical folding modulation (gyri & sulci)
      const fold = 1.0 + 0.12 * Math.sin(u * 7) * Math.cos(v * 7);

      // Separate hemispheres by pushing away from X center, pinching at the longitudinal fissure
      const sep = 16 + Math.random() * 8;
      const x = (baseRadiusX * Math.sin(u) * Math.cos(v) * 0.78 + sep) * hemiSign * fold;
      const y = (baseRadiusY * Math.cos(u) * fold) - 15; // slightly shifted up
      const z = (baseRadiusZ * Math.sin(u) * Math.sin(v) * fold) * 0.92;

      // Noise and inner cerebrum nodes (some inside the volume, some on cortical surface)
      const volumeFactor = Math.random() > 0.35 ? 1.0 : (0.45 + Math.random() * 0.5);

      const isHub = HUB_INDICES.includes(i);

      nodes.push({
        id: i,
        origX: x * volumeFactor,
        origY: y * volumeFactor,
        origZ: z * volumeFactor,
        currX: x * volumeFactor,
        currY: y * volumeFactor,
        currZ: z * volumeFactor,
        baseSize: isHub ? 4.8 : (Math.random() * 2.2 + 1.2),
        isHub,
        hubInfo: HUB_LABELS[i] || null,
        pulseOffset: Math.random() * Math.PI * 2,
        firingSpeed: 1.0 + Math.random() * 2.5,
        energy: Math.random(),
        connectedTo: []
      });
    }

    // --- 2. BUILD SYNAPTIC AXON CONNECTIONS (EDGES) ---
    const edges = [];
    const MAX_CONN_DIST = 46;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].origX - nodes[j].origX;
        const dy = nodes[i].origY - nodes[j].origY;
        const dz = nodes[i].origZ - nodes[j].origZ;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        // Connect if close enough and don't over-saturate
        if (dist < MAX_CONN_DIST && nodes[i].connectedTo.length < 4 && nodes[j].connectedTo.length < 4) {
          nodes[i].connectedTo.push(j);
          nodes[j].connectedTo.push(i);
          edges.push({
            from: i,
            to: j,
            dist,
            // Action potential impulse running along this axon
            pulseProgress: Math.random(),
            pulseSpeed: 0.008 + Math.random() * 0.02,
            active: Math.random() > 0.4
          });
        }
      }
    }

    // Add corpus callosum cross-hemisphere bridge axons
    for (let k = 0; k < 18; k++) {
      const leftNode = nodes.find(n => n.origX < -15 && Math.abs(n.origY) < 40 && Math.abs(n.origZ) < 50 && n.id % 2 === 1);
      const rightNode = nodes.find(n => n.origX > 15 && Math.abs(n.origY) < 40 && Math.abs(n.origZ) < 50 && n.id % 2 === 0);
      if (leftNode && rightNode) {
        edges.push({
          from: leftNode.id,
          to: rightNode.id,
          dist: 35,
          pulseProgress: Math.random(),
          pulseSpeed: 0.025,
          active: true,
          isBridge: true
        });
      }
    }

    // --- 3. ANIMATION RENDER LOOP ---
    const render = () => {
      time += 0.018;

      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      const fov = 420;

      // Handle gentle auto-spin when not dragging
      if (!isDraggingRef.current) {
        rotRef.current.targetY += 0.0035;
      }

      // Smooth rotation interpolation
      rotRef.current.x += (rotRef.current.targetX - rotRef.current.x) * 0.08;
      rotRef.current.y += (rotRef.current.targetY - rotRef.current.y) * 0.08;

      // Smooth mouse gaze inclination
      const gazeX = mouseGazeRef.current.x * 0.15;
      const gazeY = mouseGazeRef.current.y * 0.15;

      const finalRotX = rotRef.current.x + gazeY;
      const finalRotY = rotRef.current.y + gazeX;

      const cosY = Math.cos(finalRotY);
      const sinY = Math.sin(finalRotY);
      const cosX = Math.cos(finalRotX);
      const sinX = Math.sin(finalRotX);

      // Mode-specific color palette and energy dynamics
      const isSpeaking = mode === 'speaking';
      const isAgent = mode === 'agent' || activeTrait === 'agent';
      const isResearch = mode === 'research' || activeTrait === 'research';
      const isChatting = mode === 'chatting' || activeTrait === 'chat';

      let primaryColor = '#38bdf8'; // Cyan default
      let glowColor = 'rgba(56, 189, 248, ';
      let coreColor = 'rgba(255, 255, 255, 0.95)';
      let pulseMultiplier = 1.0;

      if (isSpeaking) {
        primaryColor = '#fbbf24'; // Warm Gold
        glowColor = 'rgba(251, 191, 36, ';
        pulseMultiplier = 1.8 + audioLevel * 1.5;
      } else if (isResearch) {
        primaryColor = '#a855f7'; // Quantum Violet
        glowColor = 'rgba(168, 85, 247, ';
        pulseMultiplier = 1.5;
      } else if (isAgent) {
        primaryColor = '#10b981'; // Emerald Matrix
        glowColor = 'rgba(16, 185, 129, ';
        pulseMultiplier = 1.35;
      } else if (isChatting) {
        primaryColor = '#38bdf8'; // Azure / Amber
        glowColor = 'rgba(56, 189, 248, ';
        pulseMultiplier = 1.15;
      }

      // 3.1 Central Thalamus Singularity (Core Glow)
      const coreR = (46 + Math.sin(time * 3) * 6) * pulseMultiplier;
      const coreGrad = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, coreR * 2.8);
      coreGrad.addColorStop(0, coreColor);
      coreGrad.addColorStop(0.25, `${glowColor}0.85)`);
      coreGrad.addColorStop(0.65, `${glowColor}0.25)`);
      coreGrad.addColorStop(1, 'rgba(0,0,0,0)');

      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreR * 2.8, 0, Math.PI * 2);
      ctx.fill();

      // 3.2 Orbital Concentric Cyber-Telemetry Rings
      const ringCount = 3;
      for (let rIdx = 0; rIdx < ringCount; rIdx++) {
        const ringRadius = (165 + rIdx * 45) * (1.0 + Math.sin(time * 2 + rIdx) * 0.02);
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(time * (rIdx % 2 === 0 ? 0.18 : -0.22));
        ctx.scale(1, Math.cos(0.85 + rIdx * 0.35 + finalRotX));

        ctx.strokeStyle = `${glowColor}${0.35 - rIdx * 0.08})`;
        ctx.lineWidth = 1.4;
        ctx.setLineDash([18, 12, 6, 12]);
        ctx.shadowColor = primaryColor;
        ctx.shadowBlur = 10;

        ctx.beginPath();
        ctx.arc(0, 0, ringRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Orbiting data packet node
        const pAngle = time * (0.8 + rIdx * 0.3) * (rIdx % 2 === 0 ? 1 : -1);
        const px = Math.cos(pAngle) * ringRadius;
        const py = Math.sin(pAngle) * ringRadius;
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ffffff';
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.arc(px, py, 3.0, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }

      // 3.3 Project 3D Nodes to 2D Screen Space
      const projected = [];
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];

        // Synaptic respiration wave
        const breath = Math.sin(time * 2.2 + n.pulseOffset) * 4 * pulseMultiplier;
        const curX = n.origX + (n.origX > 0 ? 1 : -1) * breath * 0.5;
        const curY = n.origY + Math.sin(time * 3 + n.pulseOffset) * 2;
        const curZ = n.origZ + Math.cos(time * 2.5 + n.pulseOffset) * 2;

        // 3D rotation transform
        const x1 = curX * cosY - curZ * sinY;
        const z1 = curZ * cosY + curX * sinY;
        const y2 = curY * cosX - z1 * sinX;
        const z2 = z1 * cosX + curY * sinX;

        const scale = fov / (fov + z2 + 300);
        const screenX = centerX + x1 * scale;
        const screenY = centerY + y2 * scale;

        projected.push({
          id: n.id,
          x: screenX,
          y: screenY,
          z: z2,
          scale,
          isHub: n.isHub,
          hubInfo: n.hubInfo,
          baseSize: n.baseSize,
          pulseOffset: n.pulseOffset,
          energy: n.energy
        });
      }

      // 3.4 Draw Axon Connections (Lines between neurons)
      for (let eIdx = 0; eIdx < edges.length; eIdx++) {
        const edge = edges[eIdx];
        const p1 = projected[edge.from];
        const p2 = projected[edge.to];
        if (!p1 || !p2) continue;

        // Depth average for alpha fading
        const avgZ = (p1.z + p2.z) / 2;
        const depthAlpha = Math.max(0.06, Math.min(0.7, (avgZ + 180) / 360));

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = edge.isBridge
          ? `${glowColor}${depthAlpha * 1.2})`
          : `${glowColor}${depthAlpha * 0.45})`;
        ctx.lineWidth = edge.isBridge ? 1.6 : Math.max(0.6, 1.1 * ((p1.scale + p2.scale) / 2));
        ctx.stroke();

        // Animate traveling action potential impulse
        edge.pulseProgress += edge.pulseSpeed * pulseMultiplier;
        if (edge.pulseProgress > 1.0) edge.pulseProgress = 0.0;

        const pulseX = p1.x + (p2.x - p1.x) * edge.pulseProgress;
        const pulseY = p1.y + (p2.y - p1.y) * edge.pulseProgress;
        const pulseAlpha = depthAlpha * 0.9;

        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = primaryColor;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(pulseX, pulseY, edge.isBridge ? 2.8 : 1.8, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // 3.5 Sort nodes by depth (back to front)
      projected.sort((a, b) => b.z - a.z);

      // 3.6 Draw Neuron Nodes
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        const depthRatio = Math.max(0.15, (p.z + 200) / 400);
        const radius = Math.max(0.9, p.baseSize * p.scale);

        if (p.isHub) {
          // Special Hub Node with vibrant aura
          ctx.save();
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = primaryColor;
          ctx.shadowBlur = 22;
          ctx.beginPath();
          ctx.arc(p.x, p.y, radius * 1.5, 0, Math.PI * 2);
          ctx.fill();

          // Outer pulsing halo
          const haloR = radius * (2.2 + Math.sin(time * 4 + p.pulseOffset) * 0.6);
          ctx.strokeStyle = `${glowColor}0.85)`;
          ctx.lineWidth = 1.8;
          ctx.beginPath();
          ctx.arc(p.x, p.y, haloR, 0, Math.PI * 2);
          ctx.stroke();

          // Hub Node Mini Telemetry Dot Tag
          if (p.scale > 0.85 && p.hubInfo) {
            ctx.font = 'bold 9px monospace';
            ctx.fillStyle = primaryColor;
            ctx.shadowBlur = 8;
            ctx.fillText(p.hubInfo.title.toUpperCase(), p.x + radius * 2.2, p.y + 3);
          }
          ctx.restore();
        } else {
          // Normal Neuron
          const isSpark = (p.id + Math.floor(time * 10)) % 28 === 0;
          if (isSpark) {
            ctx.fillStyle = '#ffffff';
            ctx.shadowColor = '#ffffff';
            ctx.shadowBlur = 14;
          } else {
            ctx.fillStyle = `${glowColor}${depthRatio * 0.95})`;
            ctx.shadowColor = primaryColor;
            ctx.shadowBlur = 6;
          }

          ctx.beginPath();
          ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    // Mouse Tracking for 3D Orbit Interaction
    const handleMouseDown = (e) => {
      isDraggingRef.current = true;
      lastMousePosRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
      const ny = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
      mouseGazeRef.current = { x: nx, y: ny };

      if (isDraggingRef.current) {
        const dx = e.clientX - lastMousePosRef.current.x;
        const dy = e.clientY - lastMousePosRef.current.y;
        rotRef.current.targetY += dx * 0.008;
        rotRef.current.targetX += dy * 0.008;
        lastMousePosRef.current = { x: e.clientX, y: e.clientY };
      }
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    const targetEl = containerRef.current || window;
    targetEl.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      cancelAnimationFrame(animId);
      targetEl.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [mode, audioLevel, activeTrait]);

  return (
    <div
      ref={containerRef}
      className="relative flex h-full w-full items-center justify-center cursor-grab active:cursor-grabbing select-none overflow-hidden"
    >
      <canvas
        ref={canvasRef}
        className="h-full w-full max-w-[850px] max-h-[850px] pointer-events-auto"
      />

      {/* Floating 3D Interaction Prompt HUD */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-2 pointer-events-none text-[10px] font-mono text-cyan-400/70 bg-black/40 backdrop-blur-md px-3 py-1 rounded-full border border-cyan-500/20 shadow-glow">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
        <span>DRAG TO ORBIT 360° // INTERACTIVE SYNAPTIC MESH</span>
      </div>
    </div>
  );
}
