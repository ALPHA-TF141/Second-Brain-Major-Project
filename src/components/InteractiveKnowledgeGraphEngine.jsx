import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Search,
  Filter,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Sparkles,
  Layers,
  ArrowRight,
  ExternalLink,
  MessageSquare,
  Link2,
  Plus,
  Sliders,
  X
} from 'lucide-react';

export default function InteractiveKnowledgeGraphEngine({
  onAskAI = null,
  onOpenItem = null
}) {
  const canvasRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [activeFilter, setActiveFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [aiGraphPrompt, setAiGraphPrompt] = useState('');
  const [aiHighlightedNodeIds, setAiHighlightedNodeIds] = useState(new Set());
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [showPhysics, setShowPhysics] = useState(false);

  // Physics settings
  const [physics, setPhysics] = useState({
    repulsion: 190,
    attraction: 0.05,
    gravity: 0.038,
    damping: 0.88
  });

  const simNodesRef = useRef([]);
  const simEdgesRef = useRef([]);
  const isDraggingCanvasRef = useRef(false);
  const draggedNodeRef = useRef(null);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  // Node types & color palettes (Obsidian Style with High Contrast)
  const typeConfig = {
    all: { label: 'All', color: '#94a3b8' },
    notes: { label: 'Notes', color: '#38bdf8' }, // Cyan
    projects: { label: 'Projects', color: '#a855f7' }, // Purple
    tasks: { label: 'Tasks', color: '#34d399' }, // Emerald
    documents: { label: 'Documents', color: '#fbbf24' }, // Amber
    emails: { label: 'Emails', color: '#f43f5e' }, // Rose/Red
    people: { label: 'People', color: '#ec4899' }, // Pink
    topics: { label: 'Topics', color: '#ffffff' }, // White Core
  };

  // Comprehensive knowledge graph nodes dataset
  useEffect(() => {
    const rawNodes = [
      // Core Topics
      { id: 'ml', name: 'Machine Learning', type: 'topics', notesCount: 14, projectsCount: 2, docsCount: 5, tasksCount: 3, updated: 'Today', isHub: true },
      { id: 'nn', name: 'Neural Networks', type: 'topics', notesCount: 8, projectsCount: 1, docsCount: 3, tasksCount: 1, updated: 'Today' },
      { id: 'aqi', name: 'Air Pollution Project', type: 'projects', notesCount: 7, projectsCount: 1, docsCount: 4, tasksCount: 3, updated: '2 hours ago', isHub: true },
      { id: 'rf', name: 'Random Forest Regressor', type: 'topics', notesCount: 4, projectsCount: 1, docsCount: 2, tasksCount: 1, updated: 'Yesterday' },
      { id: 'python', name: 'Python 3.12 Engine', type: 'topics', notesCount: 18, projectsCount: 3, docsCount: 6, tasksCount: 4, updated: 'Today', isHub: true },
      { id: 'dataset_aqi', name: 'Central Pollution AQI Dataset', type: 'documents', notesCount: 2, projectsCount: 1, docsCount: 1, tasksCount: 0, updated: '3 days ago' },
      { id: 'ieee_paper', name: 'IEEE Conference Research Paper', type: 'documents', notesCount: 6, projectsCount: 1, docsCount: 2, tasksCount: 2, updated: 'Today', isHub: true },
      { id: 'prof_email', name: 'Prof. Sharma (Advisor)', type: 'people', notesCount: 3, projectsCount: 2, docsCount: 1, tasksCount: 2, updated: 'Yesterday' },
      { id: 'email_deadline', name: 'Email: Project Progress Review Deadline', type: 'emails', notesCount: 1, projectsCount: 1, docsCount: 1, tasksCount: 1, updated: 'Yesterday' },
      { id: 'task_review', name: 'Task: Finalize IEEE Proposal Draft', type: 'tasks', notesCount: 2, projectsCount: 1, docsCount: 1, tasksCount: 0, updated: 'Today' },
      { id: 'task_aqi', name: 'Task: Run Random Forest on AQI Data', type: 'tasks', notesCount: 1, projectsCount: 1, docsCount: 1, tasksCount: 0, updated: 'Today' },
      { id: 'second_brain_os', name: 'Second Brain AI Operating System', type: 'projects', notesCount: 12, projectsCount: 1, docsCount: 8, tasksCount: 4, updated: 'Today', isHub: true },
      { id: 'graph_rag', name: 'GraphRAG Ingestion Architecture', type: 'notes', notesCount: 5, projectsCount: 1, docsCount: 3, tasksCount: 1, updated: 'Today' },
      { id: 'ollama_qwen', name: 'Local Ollama Qwen 2.5 Inference', type: 'topics', notesCount: 9, projectsCount: 1, docsCount: 4, tasksCount: 2, updated: 'Today' },
      { id: 'ephemeral_ocr', name: 'Ephemeral 0MB Screen Pruning', type: 'notes', notesCount: 4, projectsCount: 1, docsCount: 2, tasksCount: 1, updated: 'Today' },
      { id: 'git_vault', name: 'GitHub Memory Vault Synchronization', type: 'documents', notesCount: 6, projectsCount: 1, docsCount: 3, tasksCount: 1, updated: 'Today' },
      { id: 'karpathy_wiki', name: 'Karpathy Self-Improving Wiki Model', type: 'notes', notesCount: 8, projectsCount: 1, docsCount: 4, tasksCount: 2, updated: 'Today' },
      { id: 'youtube_scraper', name: 'Sub-Second YouTube Transcript Scraper', type: 'topics', notesCount: 3, projectsCount: 1, docsCount: 2, tasksCount: 1, updated: 'Today' },
    ];

    const rawEdges = [
      { source: 'ml', target: 'nn', label: 'specializes' },
      { source: 'ml', target: 'rf', label: 'includes' },
      { source: 'ml', target: 'python', label: 'implemented_in' },
      { source: 'aqi', target: 'ml', label: 'leverages' },
      { source: 'aqi', target: 'rf', label: 'evaluates' },
      { source: 'aqi', target: 'dataset_aqi', label: 'analyzes' },
      { source: 'aqi', target: 'prof_email', label: 'supervised_by' },
      { source: 'prof_email', target: 'email_deadline', label: 'sent' },
      { source: 'email_deadline', target: 'task_review', label: 'extracts_task' },
      { source: 'aqi', target: 'task_aqi', label: 'requires' },
      { source: 'second_brain_os', target: 'ieee_paper', label: 'documented_in' },
      { source: 'second_brain_os', target: 'graph_rag', label: 'integrates' },
      { source: 'second_brain_os', target: 'ollama_qwen', label: 'powers' },
      { source: 'second_brain_os', target: 'ephemeral_ocr', label: 'optimizes' },
      { source: 'second_brain_os', target: 'git_vault', label: 'persists_to' },
      { source: 'second_brain_os', target: 'karpathy_wiki', label: 'synthesizes_via' },
      { source: 'second_brain_os', target: 'youtube_scraper', label: 'ingests_from' },
      { source: 'graph_rag', target: 'ml', label: 'relates_to' },
      { source: 'ieee_paper', target: 'task_review', label: 'target_of' },
    ];

    // Position simulation nodes in initial cosmic cluster
    const newSimNodes = rawNodes.map((n, i) => {
      const angle = (i / rawNodes.length) * Math.PI * 2;
      const radius = n.isHub ? 80 : 170 + (Math.random() - 0.5) * 60;
      return {
        ...n,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        val: n.isHub ? 14 : 7,
        color: typeConfig[n.type]?.color || '#94a3b8'
      };
    });

    simNodesRef.current = newSimNodes;

    const nodeMap = new Map(newSimNodes.map(n => [n.id, n]));
    simEdgesRef.current = rawEdges
      .map(e => ({
        source: nodeMap.get(e.source),
        target: nodeMap.get(e.target),
        label: e.label
      }))
      .filter(e => e.source && e.target);
  }, []);

  // AI Graph Query Resolver
  const executeAiGraphQuery = (e) => {
    e?.preventDefault();
    const q = aiGraphPrompt.trim().toLowerCase();
    if (!q) {
      setAiHighlightedNodeIds(new Set());
      return;
    }

    const matchedIds = new Set();
    const simNodes = simNodesRef.current;
    const simEdges = simEdgesRef.current;

    // Find direct matching nodes
    simNodes.forEach(n => {
      if (q.includes(n.name.toLowerCase()) || n.name.toLowerCase().includes(q)) {
        matchedIds.add(n.id);
      }
      if (q.includes('pollution') && (n.id === 'aqi' || n.id === 'dataset_aqi' || n.id === 'rf' || n.id === 'ml' || n.id === 'python')) {
        matchedIds.add(n.id);
      }
      if (q.includes('ai') && (n.id === 'second_brain_os' || n.id === 'ml' || n.id === 'graph_rag' || n.id === 'ollama_qwen' || n.id === 'ieee_paper')) {
        matchedIds.add(n.id);
      }
    });

    // Also include their connected neighbors
    simEdges.forEach(({ source, target }) => {
      if (matchedIds.has(source.id)) matchedIds.add(target.id);
      if (matchedIds.has(target.id)) matchedIds.add(source.id);
    });

    setAiHighlightedNodeIds(matchedIds);
    if (matchedIds.size > 0) {
      const firstMatched = simNodes.find(n => matchedIds.has(n.id));
      if (firstMatched) setSelectedNode(firstMatched);
    }
  };

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

      const simNodes = simNodesRef.current;
      const simEdges = simEdgesRef.current;

      // 1. Force Simulation Step
      for (let i = 0; i < simNodes.length; i++) {
        const n1 = simNodes[i];
        for (let j = i + 1; j < simNodes.length; j++) {
          const n2 = simNodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);

          if (dist < 340) {
            const force = (physics.repulsion / distSq) * (n1.isHub || n2.isHub ? 1.6 : 1.0);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }
        }

        // Center gravity
        const distCenter = Math.sqrt(n1.x * n1.x + n1.y * n1.y) || 1;
        n1.vx -= (n1.x / distCenter) * (distCenter * physics.gravity * 0.05);
        n1.vy -= (n1.y / distCenter) * (distCenter * physics.gravity * 0.05);
      }

      // Spring attraction
      for (let i = 0; i < simEdges.length; i++) {
        const { source, target } = simEdges[i];
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const desired = source.isHub || target.isHub ? 95 : 65;
        const force = (dist - desired) * physics.attraction;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      }

      // Position update
      for (let i = 0; i < simNodes.length; i++) {
        const n = simNodes[i];
        if (draggedNodeRef.current === n) continue;
        n.vx *= physics.damping;
        n.vy *= physics.damping;
        n.x += n.vx;
        n.y += n.vy;
      }

      // 2. Clear & Render Background
      ctx.fillStyle = '#111318';
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      ctx.translate(width / 2 + pan.x, height / 2 + pan.y);
      ctx.scale(zoom, zoom);

      // Identify direct connections to hovered node
      const connectedNodeIds = new Set();
      if (hoveredNode) {
        connectedNodeIds.add(hoveredNode.id);
        simEdges.forEach(e => {
          if (e.source.id === hoveredNode.id) connectedNodeIds.add(e.target.id);
          if (e.target.id === hoveredNode.id) connectedNodeIds.add(e.source.id);
        });
      }

      // 3. Render Connecting Lines (Hover highlighting & dimming)
      for (let i = 0; i < simEdges.length; i++) {
        const { source, target } = simEdges[i];
        const isConnectedToHovered = hoveredNode && (source.id === hoveredNode.id || target.id === hoveredNode.id);
        const isAiHighlighted = aiHighlightedNodeIds.size > 0 && (aiHighlightedNodeIds.has(source.id) && aiHighlightedNodeIds.has(target.id));

        let strokeStyle = 'rgba(255, 255, 255, 0.12)';
        let lineWidth = 0.7;

        if (isAiHighlighted) {
          strokeStyle = 'rgba(251, 191, 36, 0.85)';
          lineWidth = 2.0;
        } else if (isConnectedToHovered) {
          strokeStyle = 'rgba(56, 189, 248, 0.9)'; // Glowing Cyan
          lineWidth = 2.2;
        } else if (hoveredNode || aiHighlightedNodeIds.size > 0) {
          strokeStyle = 'rgba(255, 255, 255, 0.02)'; // Dimmed lines
        }

        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = strokeStyle;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }

      // 4. Render Nodes (Hover size expansion & glow)
      for (let i = 0; i < simNodes.length; i++) {
        const n = simNodes[i];
        const isHovered = hoveredNode?.id === n.id;
        const isSelected = selectedNode?.id === n.id;
        const isDirectConnection = connectedNodeIds.has(n.id);
        const isAiHighlighted = aiHighlightedNodeIds.has(n.id);
        const matchesFilter = activeFilter === 'All' || n.type.toLowerCase() === activeFilter.toLowerCase();
        const matchesSearch = searchQuery ? n.name.toLowerCase().includes(searchQuery.toLowerCase()) : true;

        // Base radius & size increase on hover
        let radius = isHovered ? n.val * 1.5 : (isDirectConnection || isAiHighlighted) ? n.val * 1.25 : n.val;

        // Dimming factor
        let alpha = 1.0;
        if (!matchesFilter || !matchesSearch) {
          alpha = 0.1;
        } else if (hoveredNode && !isDirectConnection) {
          alpha = 0.18; // Dim unrelated nodes
        } else if (aiHighlightedNodeIds.size > 0 && !isAiHighlighted) {
          alpha = 0.15;
        }

        ctx.globalAlpha = alpha;

        // Glow effects
        if (isHovered || isSelected || isAiHighlighted) {
          ctx.shadowColor = isAiHighlighted ? '#fbbf24' : isHovered ? '#38bdf8' : '#ffffff';
          ctx.shadowBlur = 20;
        } else if (n.isHub) {
          ctx.shadowColor = n.color;
          ctx.shadowBlur = 8;
        }

        ctx.fillStyle = isHovered ? '#ffffff' : isAiHighlighted ? '#fbbf24' : n.color;
        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0; // Reset blur

        // Draw Labels
        if (isHovered || isSelected || isDirectConnection || isAiHighlighted || n.isHub || zoom > 1.2) {
          ctx.font = `${isHovered || isSelected ? 'bold 11px' : '9px'} Inter, sans-serif`;
          ctx.fillStyle = isHovered || isSelected ? '#ffffff' : 'rgba(230, 230, 230, 0.85)';
          ctx.textAlign = 'center';
          ctx.fillText(n.name, n.x, n.y + radius + 12);
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
  }, [physics, zoom, pan, hoveredNode, selectedNode, activeFilter, searchQuery, aiHighlightedNodeIds]);

  // Mouse & Hover Coordinate Conversion
  const getGraphPos = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    return {
      x: (clientX - (width / 2 + pan.x)) / zoom,
      y: (clientY - (height / 2 + pan.y)) / zoom,
      rawX: e.clientX,
      rawY: e.clientY
    };
  };

  const handleMouseDown = (e) => {
    const pos = getGraphPos(e);
    for (let i = simNodesRef.current.length - 1; i >= 0; i--) {
      const n = simNodesRef.current[i];
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      if (dx * dx + dy * dy < (n.val * 2.2) * (n.val * 2.2)) {
        draggedNodeRef.current = n;
        lastMouseRef.current = { x: e.clientX, y: e.clientY };
        return;
      }
    }
    isDraggingCanvasRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e) => {
    const pos = getGraphPos(e);
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

    // Hover detection with tolerance
    let found = null;
    for (let i = simNodesRef.current.length - 1; i >= 0; i--) {
      const n = simNodesRef.current[i];
      const dx = pos.x - n.x;
      const dy = pos.y - n.y;
      if (dx * dx + dy * dy < (n.val + 6) * (n.val + 6)) {
        found = n;
        break;
      }
    }
    setHoveredNode(found);
  };

  const handleMouseUp = (e) => {
    if (draggedNodeRef.current) {
      const dist = Math.abs(e.clientX - lastMouseRef.current.x) + Math.abs(e.clientY - lastMouseRef.current.y);
      if (dist < 5) {
        setSelectedNode(draggedNodeRef.current);
      }
      draggedNodeRef.current = null;
    }
    isDraggingCanvasRef.current = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.12 : 0.89;
    setZoom(prev => Math.min(3.5, Math.max(0.25, prev * factor)));
  };

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#111318] select-none text-slate-100 font-sans">
      {/* ================= 1. TOP AI + GRAPH NAVIGATION SEARCH BAR ================= */}
      <div className="absolute top-3 left-3 right-3 z-30 flex flex-wrap items-center justify-between gap-3 pointer-events-auto">
        {/* Left: AI Natural Language Graph Filter ("Show me everything connected to...") */}
        <form onSubmit={executeAiGraphQuery} className="flex items-center gap-2 rounded-xl border border-cyan-500/30 bg-black/85 px-3 py-1.5 shadow-2xl backdrop-blur-xl flex-1 max-w-lg">
          <Sparkles size={14} className="text-cyan-400 shrink-0" />
          <input
            type="text"
            value={aiGraphPrompt}
            onChange={(e) => setAiGraphPrompt(e.target.value)}
            placeholder="Ask AI: 'Show everything connected to air pollution project'..."
            className="w-full bg-transparent text-xs text-slate-100 outline-none placeholder:text-slate-500"
          />
          {aiHighlightedNodeIds.size > 0 && (
            <button
              type="button"
              onClick={() => { setAiGraphPrompt(''); setAiHighlightedNodeIds(new Set()); }}
              className="text-[10px] text-slate-400 hover:text-white"
            >
              Clear
            </button>
          )}
        </form>

        {/* Right: Quick Zoom, Reset & Physics Tools */}
        <div className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-black/80 p-1 text-slate-400 backdrop-blur-xl">
          <button
            type="button"
            onClick={() => setZoom(prev => Math.min(3.5, prev * 1.2))}
            className="p-1.5 hover:text-white rounded hover:bg-white/10 transition"
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            type="button"
            onClick={() => setZoom(prev => Math.max(0.25, prev * 0.8))}
            className="p-1.5 hover:text-white rounded hover:bg-white/10 transition"
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
          <button
            type="button"
            onClick={() => { setZoom(1.0); setPan({ x: 0, y: 0 }); }}
            className="p-1.5 hover:text-white rounded hover:bg-white/10 transition"
            title="Center Graph"
          >
            <Maximize2 size={14} />
          </button>
          <button
            type="button"
            onClick={() => setShowPhysics(!showPhysics)}
            className={`p-1.5 rounded transition ${showPhysics ? 'text-cyan-400 bg-white/10' : 'hover:text-white'}`}
            title="Physics Simulation Controls"
          >
            <Sliders size={14} />
          </button>
        </div>
      </div>

      {/* ================= 2. TOP FILTER PILLS (ALL, NOTES, PROJECTS, TASKS...) ================= */}
      <div className="absolute top-14 left-3 z-20 flex flex-wrap items-center gap-1.5 pointer-events-auto">
        {Object.entries(typeConfig).map(([key, config]) => {
          const isSelected = activeFilter.toLowerCase() === key.toLowerCase();
          return (
            <button
              key={key}
              type="button"
              onClick={() => setActiveFilter(config.label)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-semibold transition backdrop-blur-md border ${
                isSelected
                  ? 'border-cyan-400 bg-cyan-500/20 text-white shadow-glow'
                  : 'border-white/5 bg-black/50 text-slate-400 hover:text-white hover:bg-white/10'
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: config.color }} />
              <span>{config.label}</span>
            </button>
          );
        })}
      </div>

      {/* ================= 3. HOVER FLOATING PREVIEW PANEL (SECTION 3 SPEC) ================= */}
      {hoveredNode && !draggedNodeRef.current && (
        <div className="pointer-events-none absolute bottom-5 left-5 z-40 w-72 rounded-xl border border-cyan-500/30 bg-black/90 p-3.5 shadow-2xl backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-100">
          <div className="flex items-center gap-2 border-b border-white/10 pb-2 mb-2">
            <span className="h-2.5 w-2.5 rounded-full shadow-[0_0_8px]" style={{ backgroundColor: hoveredNode.color, shadowColor: hoveredNode.color }} />
            <h4 className="text-xs font-bold text-white truncate">{hoveredNode.name}</h4>
          </div>

          <div className="text-[11px] font-mono text-cyan-300 mb-1.5">
            {hoveredNode.notesCount + hoveredNode.projectsCount + hoveredNode.docsCount + hoveredNode.tasksCount} Connected items
          </div>

          <div className="grid grid-cols-3 gap-1.5 text-[10px] font-mono text-slate-400 mb-2">
            <div className="rounded bg-white/5 p-1 text-center">
              <span className="text-white block font-bold">{hoveredNode.notesCount}</span> Notes
            </div>
            <div className="rounded bg-white/5 p-1 text-center">
              <span className="text-white block font-bold">{hoveredNode.projectsCount}</span> Projects
            </div>
            <div className="rounded bg-white/5 p-1 text-center">
              <span className="text-white block font-bold">{hoveredNode.docsCount}</span> Docs
            </div>
          </div>

          <div className="text-[10px] text-slate-500 border-t border-white/5 pt-1.5 flex justify-between">
            <span>Last updated: {hoveredNode.updated}</span>
            <span className="text-cyan-400">Click to inspect</span>
          </div>
        </div>
      )}

      {/* ================= 4. CLICK DETAIL INSPECTOR PANEL (SECTION 4 SPEC) ================= */}
      {selectedNode && (
        <div className="absolute top-4 bottom-4 right-4 z-40 w-84 rounded-2xl border border-cyan-500/30 bg-[#070b18]/95 p-5 shadow-2xl backdrop-blur-2xl flex flex-col justify-between overflow-y-auto thin-scrollbar">
          <div>
            <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-3">
              <div className="flex items-center gap-2 truncate">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: selectedNode.color }} />
                <h3 className="text-sm font-bold text-white truncate">{selectedNode.name}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedNode(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
              >
                <X size={14} />
              </button>
            </div>

            {/* Connected Knowledge Breakdown */}
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold tracking-wider">Related Quantities</span>
                <div className="grid grid-cols-4 gap-1.5 mt-1 text-[11px] font-mono text-center">
                  <div className="p-1.5 rounded-lg bg-white/5 border border-white/5">
                    <span className="text-purple-400 font-bold block">{selectedNode.projectsCount}</span> Proj
                  </div>
                  <div className="p-1.5 rounded-lg bg-white/5 border border-white/5">
                    <span className="text-cyan-400 font-bold block">{selectedNode.notesCount}</span> Notes
                  </div>
                  <div className="p-1.5 rounded-lg bg-white/5 border border-white/5">
                    <span className="text-amber-400 font-bold block">{selectedNode.docsCount}</span> Docs
                  </div>
                  <div className="p-1.5 rounded-lg bg-white/5 border border-white/5">
                    <span className="text-emerald-400 font-bold block">{selectedNode.tasksCount}</span> Tasks
                  </div>
                </div>
              </div>

              {/* Connected Concepts Chips */}
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold tracking-wider">Immediate Connections</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {['Neural Networks', 'Regression', 'Random Forest', 'Python', 'Air Pollution Project'].map((item) => (
                    <span key={item} className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons (Section 4 Specification) */}
          <div className="space-y-2 border-t border-white/10 pt-3 mt-4">
            <button
              type="button"
              onClick={() => onOpenItem?.(selectedNode)}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-3 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-300 shadow-glow"
            >
              <ExternalLink size={13} />
              Open Knowledge Entity
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => onAskAI?.(selectedNode.name)}
                className="flex items-center justify-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-semibold text-slate-200 hover:bg-white/10 transition"
              >
                <Sparkles size={12} className="text-amber-400" />
                Ask AI
              </button>
              <button
                type="button"
                onClick={() => {
                  setPan({ x: -selectedNode.x * zoom, y: -selectedNode.y * zoom });
                  setZoom(1.4);
                }}
                className="flex items-center justify-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[11px] font-semibold text-slate-200 hover:bg-white/10 transition"
              >
                <Maximize2 size={12} />
                Focus
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Physics Sliders Drawer */}
      {showPhysics && (
        <div className="absolute top-14 right-3 z-30 w-56 rounded-xl border border-white/10 bg-black/90 p-3.5 text-xs text-slate-300 shadow-2xl backdrop-blur-xl space-y-2">
          <div className="font-bold text-slate-200 border-b border-white/10 pb-1 text-[10px] uppercase font-mono">
            Forces Simulation
          </div>
          <div>
            <div className="flex justify-between text-[10px] text-slate-400 mb-1">
              <span>Repulsion</span>
              <span>{physics.repulsion}</span>
            </div>
            <input
              type="range"
              min="80"
              max="450"
              value={physics.repulsion}
              onChange={(e) => setPhysics(p => ({ ...p, repulsion: Number(e.target.value) }))}
              className="w-full accent-cyan-400"
            />
          </div>
          <div>
            <div className="flex justify-between text-[10px] text-slate-400 mb-1">
              <span>Spring Attraction</span>
              <span>{(physics.attraction * 100).toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="0.1"
              step="0.005"
              value={physics.attraction}
              onChange={(e) => setPhysics(p => ({ ...p, attraction: Number(e.target.value) }))}
              className="w-full accent-cyan-400"
            />
          </div>
        </div>
      )}

      {/* Interactive Physics Canvas */}
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
