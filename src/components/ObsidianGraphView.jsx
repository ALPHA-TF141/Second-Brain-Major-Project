import { useEffect, useRef, useState, useCallback } from 'react';
import { Search, Sliders, RefreshCw, ZoomIn, ZoomOut, Maximize2, Sparkles, Filter } from 'lucide-react';

export default function ObsidianGraphView({
  nodes = [],
  edges = [],
  onSelectNode = null,
  activeFilter = ''
}) {
  const canvasRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [showSettings, setShowSettings] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Physics simulation parameters
  const [physics, setPhysics] = useState({
    repulsion: 180,
    attraction: 0.045,
    gravity: 0.035,
    damping: 0.88
  });

  const simNodesRef = useRef([]);
  const simEdgesRef = useRef([]);
  const isDraggingCanvasRef = useRef(false);
  const draggedNodeRef = useRef(null);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  // Color mapping based on node domain / category (Obsidian Palette)
  const getDomainColor = (domain = '') => {
    const d = domain.toLowerCase();
    if (d.includes('tech') || d.includes('ai') || d.includes('code')) return '#38bdf8'; // Cyan/Sky
    if (d.includes('science') || d.includes('physics')) return '#4ade80'; // Emerald Green
    if (d.includes('geopolitic') || d.includes('security') || d.includes('cyber')) return '#f87171'; // Coral Red
    if (d.includes('research') || d.includes('paper')) return '#fbbf24'; // Amber Gold
    if (d.includes('core')) return '#ffffff'; // White Central Core
    return '#94a3b8'; // Slate Grey
  };

  // Initialize or update force simulation nodes
  useEffect(() => {
    const existingMap = new Map(simNodesRef.current.map(n => [n.id, n]));
    const width = canvasRef.current?.clientWidth || 900;
    const height = canvasRef.current?.clientHeight || 650;

    const newSimNodes = nodes.map((node, i) => {
      const existing = existingMap.get(node.id);
      if (existing) {
        existing.val = node.val || 8;
        existing.domain = node.domain || node.type || 'General';
        existing.label = node.label || node.name || node.id;
        return existing;
      }

      // Initial clustered spherical layout with random jitter
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * 260 + 40;
      const isHub = node.priority === 'high' || (node.val && node.val > 12);

      return {
        id: node.id,
        label: node.label || node.name || node.id,
        domain: node.domain || node.type || 'General',
        summary: node.summary || '',
        hero_image: node.hero_image || null,
        val: isHub ? 14 : Math.random() * 4 + 4,
        x: Math.cos(angle) * radius + (Math.random() - 0.5) * 40,
        y: Math.sin(angle) * radius + (Math.random() - 0.5) * 40,
        vx: 0,
        vy: 0,
        color: getDomainColor(node.domain || node.type),
        isHub
      };
    });

    simNodesRef.current = newSimNodes;

    // Map edges to simulation nodes
    const nodeById = new Map(newSimNodes.map(n => [n.id, n]));
    const newSimEdges = edges
      .map(edge => ({
        source: nodeById.get(edge.source_id || edge.source),
        target: nodeById.get(edge.target_id || edge.target),
        label: edge.relationship_type || edge.label || ''
      }))
      .filter(e => e.source && e.target);

    simEdgesRef.current = newSimEdges;
  }, [nodes, edges]);

  // Main Canvas Render & Physics Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      // 1. Physics Step (Force-Directed Calculation)
      const simNodes = simNodesRef.current;
      const simEdges = simEdgesRef.current;

      // Repulsion between all node pairs
      for (let i = 0; i < simNodes.length; i++) {
        const n1 = simNodes[i];
        for (let j = i + 1; j < simNodes.length; j++) {
          const n2 = simNodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);

          if (dist < 320) {
            const force = (physics.repulsion / distSq) * (n1.isHub || n2.isHub ? 1.8 : 1.0);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }
        }

        // Central gravity (pull towards center)
        const distFromCenter = Math.sqrt(n1.x * n1.x + n1.y * n1.y) || 1;
        n1.vx -= (n1.x / distFromCenter) * (distFromCenter * physics.gravity * 0.05);
        n1.vy -= (n1.y / distFromCenter) * (distFromCenter * physics.gravity * 0.05);
      }

      // Spring attraction along edges
      for (let i = 0; i < simEdges.length; i++) {
        const { source, target } = simEdges[i];
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const desiredDist = source.isHub || target.isHub ? 80 : 55;
        const force = (dist - desiredDist) * physics.attraction;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      }

      // Position update with damping
      for (let i = 0; i < simNodes.length; i++) {
        const n = simNodes[i];
        if (draggedNodeRef.current === n) continue; // Skip position update if user is dragging node

        n.vx *= physics.damping;
        n.vy *= physics.damping;
        n.x += n.vx;
        n.y += n.vy;
      }

      // 2. Clear & Set Background (Obsidian #161616 / #1e1e1e)
      ctx.fillStyle = '#181818';
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      ctx.translate(width / 2 + pan.x, height / 2 + pan.y);
      ctx.scale(zoom, zoom);

      // 3. Draw Synaptic Edges
      for (let i = 0; i < simEdges.length; i++) {
        const { source, target } = simEdges[i];
        const isConnectedToHovered = hoveredNode && (hoveredNode.id === source.id || hoveredNode.id === target.id);

        ctx.lineWidth = isConnectedToHovered ? 1.5 : 0.6;
        ctx.strokeStyle = isConnectedToHovered
          ? 'rgba(56, 189, 248, 0.75)'
          : hoveredNode
          ? 'rgba(255, 255, 255, 0.03)'
          : 'rgba(255, 255, 255, 0.12)';

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }

      // 4. Draw Nodes (Obsidian Circles with Halo Glow)
      for (let i = 0; i < simNodes.length; i++) {
        const n = simNodes[i];
        const isHovered = hoveredNode?.id === n.id;
        const isMatched = searchQuery
          ? n.label.toLowerCase().includes(searchQuery.toLowerCase())
          : true;

        const radius = isHovered ? n.val * 1.4 : n.val;
        const alpha = !isMatched ? 0.15 : hoveredNode && !isHovered ? 0.45 : 1.0;

        // Outer glow on hover or hubs
        if (isHovered || n.isHub) {
          ctx.shadowColor = n.color;
          ctx.shadowBlur = isHovered ? 18 : 8;
        }

        ctx.fillStyle = isHovered ? '#ffffff' : n.color;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0; // Reset blur

        // Draw Text Labels for Hubs, Hovered Nodes, or when zoomed in
        if (isHovered || n.isHub || zoom > 1.3 || (isMatched && searchQuery)) {
          ctx.font = `${isHovered || n.isHub ? 'bold 10px' : '9px'} Inter, sans-serif`;
          ctx.fillStyle = isHovered ? '#ffffff' : 'rgba(240, 240, 240, 0.85)';
          ctx.textAlign = 'center';
          ctx.fillText(n.label, n.x, n.y + radius + 11);
        }

        ctx.globalAlpha = 1.0;
      }

      ctx.restore();
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [physics, zoom, pan, hoveredNode, searchQuery]);

  // Mouse Interactions (Pan, Zoom, Drag Node, Click to Select)
  const getCanvasMousePos = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    // Inverse transform to graph coordinate space
    const x = (clientX - (width / 2 + pan.x)) / zoom;
    const y = (clientY - (height / 2 + pan.y)) / zoom;
    return { x, y, rawX: e.clientX, rawY: e.clientY };
  };

  const handleMouseDown = (e) => {
    const pos = getCanvasMousePos(e);

    // Check if clicked on a node
    for (let i = simNodesRef.current.length - 1; i >= 0; i--) {
      const n = simNodesRef.current[i];
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      if (dx * dx + dy * dy < (n.val * 2) * (n.val * 2)) {
        draggedNodeRef.current = n;
        lastMouseRef.current = { x: e.clientX, y: e.clientY };
        return;
      }
    }

    // Otherwise drag canvas
    isDraggingCanvasRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e) => {
    const pos = getCanvasMousePos(e);

    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = pos.x;
      draggedNodeRef.current.y = pos.y;
      draggedNodeRef.current.vx = 0;
      draggedNodeRef.current.vy = 0;
      return;
    }

    if (isDraggingCanvasRef.current) {
      const dx = e.clientX - lastMouseRef.current.x;
      const dy = e.clientY - lastMouseRef.current.y;
      setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
      lastMouseRef.current = { x: e.clientX, y: e.clientY };
      return;
    }

    // Hover detection
    let found = null;
    for (let i = simNodesRef.current.length - 1; i >= 0; i--) {
      const n = simNodesRef.current[i];
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      if (dx * dx + dy * dy < (n.val + 4) * (n.val + 4)) {
        found = n;
        break;
      }
    }
    setHoveredNode(found);
  };

  const handleMouseUp = (e) => {
    if (draggedNodeRef.current) {
      // If it was a fast click without move, select the node
      const dist = Math.abs(e.clientX - lastMouseRef.current.x) + Math.abs(e.clientY - lastMouseRef.current.y);
      if (dist < 5) {
        onSelectNode?.(draggedNodeRef.current);
      }
      draggedNodeRef.current = null;
    }
    isDraggingCanvasRef.current = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    setZoom(prev => Math.min(3.5, Math.max(0.25, prev * zoomFactor)));
  };

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#181818] select-none rounded-xl border border-white/5">
      {/* Top Floating Controls Bar (Obsidian Style) */}
      <div className="absolute top-3 left-3 z-20 flex items-center gap-2">
        {/* Search Input */}
        <div className="relative flex items-center">
          <Search size={13} className="pointer-events-none absolute left-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter nodes..."
            className="h-8 w-44 rounded-md border border-white/10 bg-black/60 pl-8 pr-3 text-xs text-slate-200 outline-none focus:w-56 focus:border-cyan-400 transition-all placeholder:text-slate-500"
          />
        </div>

        {/* Legend Pills */}
        <div className="hidden sm:flex items-center gap-2 rounded-md border border-white/10 bg-black/40 px-3 py-1 text-[10px] text-slate-300">
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#38bdf8]" /> Tech & AI</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#4ade80]" /> Science</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#f87171]" /> Cyber & Defense</span>
          <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#fbbf24]" /> Research</span>
        </div>
      </div>

      {/* Top Right Tool Buttons */}
      <div className="absolute top-3 right-3 z-20 flex items-center gap-1 rounded-md border border-white/10 bg-black/50 p-1 text-slate-400">
        <button
          type="button"
          onClick={() => setZoom(prev => Math.min(3.5, prev * 1.2))}
          className="p-1 hover:text-white rounded hover:bg-white/10 transition"
          title="Zoom In"
        >
          <ZoomIn size={14} />
        </button>
        <button
          type="button"
          onClick={() => setZoom(prev => Math.max(0.25, prev * 0.8))}
          className="p-1 hover:text-white rounded hover:bg-white/10 transition"
          title="Zoom Out"
        >
          <ZoomOut size={14} />
        </button>
        <button
          type="button"
          onClick={() => { setZoom(1.0); setPan({ x: 0, y: 0 }); }}
          className="p-1 hover:text-white rounded hover:bg-white/10 transition"
          title="Reset View"
        >
          <Maximize2 size={14} />
        </button>
        <button
          type="button"
          onClick={() => setShowSettings(!showSettings)}
          className={`p-1 rounded transition ${showSettings ? 'text-cyan-400 bg-white/10' : 'hover:text-white hover:bg-white/10'}`}
          title="Graph Forces & Physics"
        >
          <Sliders size={14} />
        </button>
      </div>

      {/* Physics Settings Drawer (Obsidian Slider Panel) */}
      {showSettings && (
        <div className="absolute top-12 right-3 z-30 w-52 rounded-lg border border-white/10 bg-black/85 p-3 text-xs text-slate-300 shadow-2xl backdrop-blur-xl space-y-2.5">
          <div className="font-bold text-slate-200 border-b border-white/10 pb-1.5 uppercase text-[10px] tracking-wider">
            Forces Simulation
          </div>
          <div>
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>Node Repulsion</span>
              <span>{physics.repulsion}</span>
            </div>
            <input
              type="range"
              min="50"
              max="400"
              value={physics.repulsion}
              onChange={(e) => setPhysics(prev => ({ ...prev, repulsion: Number(e.target.value) }))}
              className="w-full accent-cyan-400"
            />
          </div>
          <div>
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>Link Attraction</span>
              <span>{(physics.attraction * 100).toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.1"
              step="0.005"
              value={physics.attraction}
              onChange={(e) => setPhysics(prev => ({ ...prev, attraction: Number(e.target.value) }))}
              className="w-full accent-cyan-400"
            />
          </div>
          <div>
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>Center Gravity</span>
              <span>{(physics.gravity * 100).toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.08"
              step="0.005"
              value={physics.gravity}
              onChange={(e) => setPhysics(prev => ({ ...prev, gravity: Number(e.target.value) }))}
              className="w-full accent-cyan-400"
            />
          </div>
        </div>
      )}

      {/* Hover Node Tooltip */}
      {hoveredNode && (
        <div className="pointer-events-none absolute bottom-4 left-4 z-20 max-w-sm rounded-lg border border-white/15 bg-black/85 p-2.5 shadow-2xl backdrop-blur-md">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: hoveredNode.color }} />
            <h4 className="text-xs font-bold text-white">{hoveredNode.label}</h4>
            <span className="rounded bg-white/10 px-1.5 py-0.5 text-[9px] text-cyan-300 uppercase">{hoveredNode.domain}</span>
          </div>
          {hoveredNode.summary && (
            <p className="mt-1 text-[11px] leading-tight text-slate-400 line-clamp-2">{hoveredNode.summary}</p>
          )}
        </div>
      )}

      {/* Interactive Canvas */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="h-full w-full cursor-grab active:cursor-grabbing"
      />
    </div>
  );
}
