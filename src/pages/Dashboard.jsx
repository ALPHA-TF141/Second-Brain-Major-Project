import { useEffect, useState } from 'react';
import { Sliders, Filter, Search, Sparkles, ExternalLink, RefreshCw, Layers } from 'lucide-react';
import ObsidianGraphView from '../components/ObsidianGraphView.jsx';
import { useBackend } from '../context/BackendContext.jsx';

export default function Dashboard() {
  const { apiClient, username } = useBackend();
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedCardImage, setSelectedCardImage] = useState(null);

  // Load live nodes and edges from Memory Vault
  useEffect(() => {
    let active = true;
    async function loadData() {
      try {
        const res = await fetch(`${apiClient.baseUrl}/api/graph/vault`);
        if (res.ok) {
          const vaultData = await res.json();
          if (active && vaultData && Array.isArray(vaultData.nodes)) {
            setGraphNodes(vaultData.nodes);
            setGraphEdges(vaultData.edges || []);
          }
        }
      } catch {
        // Backend booting
      }
    }

    loadData();
    const interval = setInterval(loadData, 6000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [apiClient]);

  return (
    <div className="relative flex h-full w-full flex-col bg-[#1e1e1e] overflow-hidden select-none">
      {/* Obsidian Graph View Subheader Bar */}
      <div className="flex h-8 shrink-0 items-center justify-between border-b border-[#262626] bg-[#1a1a1a] px-3.5 text-xs text-[#a0a0a0]">
        <div className="flex items-center gap-2 font-medium">
          <span className="text-white">Graph view</span>
          <span className="text-slate-600">/</span>
          <span className="text-slate-500 font-mono text-[11px]">{graphNodes.length} nodes · {graphEdges.length} links</span>
        </div>

        <div className="flex items-center gap-2 text-slate-400">
          <span className="text-[10px] text-emerald-400 font-mono">● {username || 'Immanuel'} Active</span>
        </div>
      </div>

      {/* Massive Full-Bleed Obsidian Force-Directed Clustered Knowledge Graph */}
      <div className="relative flex-1 h-full w-full bg-[#181818] overflow-hidden">
        <ObsidianGraphView
          nodes={graphNodes}
          edges={graphEdges}
          onSelectNode={(node) => setSelectedNode(node)}
        />

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <div className="absolute top-4 right-4 z-30 w-80 rounded-xl border border-white/15 bg-black/90 p-4 shadow-2xl backdrop-blur-2xl text-xs space-y-3">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <div>
                <span className="rounded bg-cyan-400/10 px-2 py-0.5 text-[10px] font-bold uppercase text-cyan-400">
                  {selectedNode.domain || 'Node'}
                </span>
                <h4 className="mt-1 text-sm font-bold text-white">{selectedNode.label}</h4>
              </div>
              <button
                type="button"
                onClick={() => setSelectedNode(null)}
                className="rounded p-1 text-slate-400 hover:text-white hover:bg-white/10"
              >
                &times;
              </button>
            </div>

            {selectedNode.hero_image && (
              <div
                onClick={() => setSelectedCardImage(`${apiClient.baseUrl}/${selectedNode.hero_image.replace(/\\/g, '/')}`)}
                className="relative h-32 w-full cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-black"
              >
                <img
                  src={`${apiClient.baseUrl}/${selectedNode.hero_image.replace(/\\/g, '/')}`}
                  alt={selectedNode.label}
                  className="h-full w-full object-cover hover:scale-105 transition"
                />
              </div>
            )}

            <p className="text-slate-300 leading-relaxed text-[11.5px]">
              {selectedNode.summary || 'Cognitive node synthesized into your Obsidian memory graph.'}
            </p>

            <div className="border-t border-white/10 pt-2 flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>Connected to Vault</span>
              <span className="text-cyan-400">ID: {String(selectedNode.id).slice(0, 14)}</span>
            </div>
          </div>
        )}
      </div>

      {/* Full-Screen Image Lightbox Modal */}
      {selectedCardImage && (
        <div
          onClick={() => setSelectedCardImage(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div className="relative max-h-[92vh] max-w-[92vw] overflow-hidden rounded-2xl border border-white/20 bg-slate-950 p-3 shadow-2xl">
            <img src={selectedCardImage} alt="Hero Capture" className="max-h-[84vh] w-auto rounded-xl object-contain" />
            <div className="mt-3 flex items-center justify-between px-2 text-xs text-slate-400">
              <span>Hero Screen Capture · Immanuel's Memory Layer</span>
              <button
                type="button"
                onClick={() => setSelectedCardImage(null)}
                className="rounded-lg bg-white/10 px-3.5 py-1.5 font-bold text-slate-200 transition hover:bg-white/20"
              >
                Close (Esc)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
