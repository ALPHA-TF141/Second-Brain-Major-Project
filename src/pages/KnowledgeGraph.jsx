import React, { useState, useEffect, useCallback } from 'react';
import GraphVisualization from '../components/GraphVisualization';
import NodeDetailsPanel from '../components/NodeDetailsPanel';
import FilterPanel from '../components/FilterPanel';
import RecommendationPanel from '../components/RecommendationPanel';
import PageHeader from '../components/PageHeader.jsx';
import { useBackend } from '../context/BackendContext.jsx';
import { Network, Sparkles, RefreshCw, Layers } from 'lucide-react';
import '../styles/knowledge-graph.css';

export default function KnowledgeGraphPage() {
  const { apiClient, loginDemo } = useBackend();
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({
    nodeType: null,
    minImportance: 0,
    minStrength: 0,
    searchQuery: ''
  });
  const [activeView, setActiveView] = useState('graph');
  const [recommendations, setRecommendations] = useState([]);

  async function ensureLogin() {
    if (!apiClient.getToken()) await loginDemo();
  }

  const loadGraphData = async () => {
    setLoading(true);
    try {
      await ensureLogin();
      const token = apiClient.getToken();
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      };

      const [nodesRes, edgesRes, statsRes] = await Promise.all([
        fetch(`${apiClient.baseUrl}/api/graph/nodes?limit=150`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${apiClient.baseUrl}/api/graph/edges?limit=250`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${apiClient.baseUrl}/api/graph/stats`, { headers }).then(r => r.json()).catch(() => null)
      ]);

      const validNodes = Array.isArray(nodesRes) ? nodesRes : [];
      const validEdges = Array.isArray(edgesRes) ? edgesRes : [];

      setNodes(validNodes);
      setEdges(validEdges);
      setStats(statsRes);

      if (activeView === 'clusters') {
        loadClusters();
      }
    } catch (error) {
      console.error('Error loading graph data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadClusters = async () => {
    try {
      const token = apiClient.getToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${apiClient.baseUrl}/api/graph/clusters`, { headers });
      const data = await res.json();
      setClusters(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading clusters:', error);
    }
  };

  const fetchRecommendations = async (memoryId) => {
    try {
      const token = apiClient.getToken();
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${apiClient.baseUrl}/api/graph/recommendations/related-memories/${memoryId}`, { headers });
      const data = await res.json();
      setRecommendations(data.related_memories || []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  useEffect(() => {
    loadGraphData();
  }, []);

  useEffect(() => {
    if (selectedNode && selectedNode.type === 'memory') {
      fetchRecommendations(selectedNode.id);
    }
  }, [selectedNode]);

  const generateGraph = async () => {
    setLoading(true);
    try {
      await ensureLogin();
      const token = apiClient.getToken();
      await fetch(`${apiClient.baseUrl}/api/graph/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ limit: 1000 })
      });
      await loadGraphData();
    } catch (error) {
      console.error('Error generating graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterNodes = useCallback(() => {
    return nodes.filter(node => {
      if (filters.nodeType && node.type !== filters.nodeType) return false;
      if (node.importance < filters.minImportance) return false;
      if (filters.searchQuery && !node.name.toLowerCase().includes(filters.searchQuery.toLowerCase())) return false;
      return true;
    });
  }, [nodes, filters]);

  const filteredNodes = filterNodes();
  const filteredEdges = edges.filter(edge => {
    if (edge.strength < filters.minStrength) return false;
    const edgeNodeIds = new Set(filteredNodes.map(n => n.id));
    return edgeNodeIds.has(edge.source_id) && edgeNodeIds.has(edge.target_id);
  });

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Neural Knowledge Network"
        title="Dynamic Cognitive Knowledge Graph"
        description="Explore the interconnected nodes of science, technology, concepts, and memory cards synthesized by Jarvis."
        action={
          <div className="flex gap-2">
            <button
              type="button"
              onClick={loadGraphData}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-300 transition hover:bg-white/10"
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              Refresh Graph
            </button>
            <button
              type="button"
              onClick={generateGraph}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg border border-cyanGlow/30 bg-cyanGlow/10 px-3 py-2 text-xs font-bold text-cyanGlow transition hover:bg-cyanGlow/20"
            >
              <Sparkles size={13} />
              Re-Cluster Nodes
            </button>
          </div>
        }
      />

      {/* View Switcher & Quick Stats Bar */}
      <div className="glass-panel flex flex-wrap items-center justify-between gap-3 rounded-lg p-3">
        <div className="flex items-center gap-1 rounded-lg bg-black/40 p-1">
          {['graph', 'clusters', 'stats'].map((view) => (
            <button
              key={view}
              onClick={() => setActiveView(view)}
              className={`rounded px-3 py-1 text-xs font-semibold capitalize transition ${
                activeView === view
                  ? 'bg-cyanGlow text-slate-950 font-bold shadow-glow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {view}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4 text-xs font-medium text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-cyanGlow"></span>
            {filteredNodes.length} Active Nodes
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-mintGlow"></span>
            {filteredEdges.length} Synaptic Edges
          </span>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
        <FilterPanel
          filters={filters}
          onFilterChange={setFilters}
          nodeTypes={Array.from(new Set(nodes.map(n => n.type)))}
        />

        <div className="glass-panel min-h-[580px] rounded-lg p-4">
          {activeView === 'graph' && (
            <div className="relative h-[550px] w-full overflow-hidden rounded-lg border border-white/5 bg-slate-950/80">
              <GraphVisualization
                nodes={filteredNodes}
                edges={filteredEdges}
                onNodeClick={setSelectedNode}
                selectedNode={selectedNode}
              />
            </div>
          )}

          {activeView === 'clusters' && (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {clusters.map((cluster) => (
                <div key={cluster.id} className="rounded-lg border border-white/10 bg-white/5 p-4">
                  <h4 className="font-semibold text-slate-200">{cluster.name}</h4>
                  <p className="mt-1 text-xs text-cyanGlow">{cluster.primary_topic}</p>
                  <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                    <span>{cluster.size} Concepts</span>
                    <span>Cohesion: {(cluster.cohesion * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
              {clusters.length === 0 && (
                <div className="col-span-full py-12 text-center text-sm text-slate-500">
                  Clusters will organize as more cards are captured.
                </div>
              )}
            </div>
          )}

          {activeView === 'stats' && stats && (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-center">
                  <p className="text-xs text-slate-500 uppercase">Total Nodes</p>
                  <h3 className="text-2xl font-bold text-cyanGlow">{stats.total_nodes}</h3>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-center">
                  <p className="text-xs text-slate-500 uppercase">Synaptic Edges</p>
                  <h3 className="text-2xl font-bold text-mintGlow">{stats.total_edges}</h3>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-center">
                  <p className="text-xs text-slate-500 uppercase">Domain Clusters</p>
                  <h3 className="text-2xl font-bold text-amberGlow">{stats.total_clusters}</h3>
                </div>
              </div>

              {stats.top_nodes && stats.top_nodes.length > 0 && (
                <div className="rounded-lg border border-white/10 bg-white/5 p-4">
                  <h4 className="mb-3 text-sm font-semibold text-slate-300">Top Synaptic Concepts</h4>
                  <div className="space-y-2">
                    {stats.top_nodes.slice(0, 8).map((node, i) => (
                      <div key={i} className="flex items-center justify-between text-xs text-slate-300">
                        <span className="font-semibold">{node.name}</span>
                        <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] text-cyanGlow">{node.type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {selectedNode && (
        <NodeDetailsPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}

      {recommendations.length > 0 && (
        <RecommendationPanel
          recommendations={recommendations}
          title="Related Memories"
        />
      )}
    </div>
  );
}
