import React, { useState, useEffect, useCallback } from 'react';
import GraphVisualization from '../components/GraphVisualization';
import NodeDetailsPanel from '../components/NodeDetailsPanel';
import FilterPanel from '../components/FilterPanel';
import RecommendationPanel from '../components/RecommendationPanel';
import '../styles/knowledge-graph.css';

export default function KnowledgeGraphPage() {
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
  const [activeView, setActiveView] = useState('graph'); // 'graph', 'clusters', 'timeline', 'stats'
  const [recommendations, setRecommendations] = useState([]);

  // Load graph data on component mount
  useEffect(() => {
    loadGraphData();
  }, []);

  // Fetch recommendations when node is selected
  useEffect(() => {
    if (selectedNode && selectedNode.type === 'memory') {
      fetchRecommendations(selectedNode.id);
    }
  }, [selectedNode]);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      // Fetch all nodes and edges
      const nodesRes = await fetch('/api/graph/nodes', {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const nodesData = await nodesRes.json();

      const edgesRes = await fetch('/api/graph/edges', {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const edgesData = await edgesRes.json();

      const statsRes = await fetch('/api/graph/stats', {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const statsData = await statsRes.json();

      setNodes(nodesData);
      setEdges(edgesData);
      setStats(statsData);

      // Load clusters if viewing clusters
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
      const res = await fetch('/api/graph/clusters', {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const data = await res.json();
      setClusters(data);
    } catch (error) {
      console.error('Error loading clusters:', error);
    }
  };

  const fetchRecommendations = async (memoryId) => {
    try {
      const res = await fetch(`/api/graph/recommendations/related-memories/${memoryId}`, {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const data = await res.json();
      setRecommendations(data.related_memories || []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  const generateGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/graph/generate', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`
        },
        body: JSON.stringify({ limit: 1000 })
      });
      const data = await res.json();
      console.log('Graph generated:', data.stats);
      loadGraphData();
    } catch (error) {
      console.error('Error generating graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const clusterGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/graph/clustering/similarity', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ threshold: 0.6 })
      });
      const data = await res.json();
      console.log('Clustering complete:', data);
      loadClusters();
    } catch (error) {
      console.error('Error clustering:', error);
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
    <div className="knowledge-graph-page">
      <div className="graph-header">
        <h1>Knowledge Graph</h1>
        <p>Your interconnected learning network</p>
      </div>

      <div className="graph-toolbar">
        <div className="toolbar-left">
          <button 
            onClick={generateGraph} 
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? 'Generating...' : 'Generate Graph'}
          </button>
          <button 
            onClick={clusterGraph}
            disabled={loading}
            className="btn btn-secondary"
          >
            Cluster Concepts
          </button>
        </div>

        <div className="toolbar-center">
          <div className="view-buttons">
            <button 
              className={`view-btn ${activeView === 'graph' ? 'active' : ''}`}
              onClick={() => setActiveView('graph')}
            >
              Graph
            </button>
            <button 
              className={`view-btn ${activeView === 'clusters' ? 'active' : ''}`}
              onClick={() => setActiveView('clusters')}
            >
              Clusters
            </button>
            <button 
              className={`view-btn ${activeView === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveView('stats')}
            >
              Stats
            </button>
          </div>
        </div>

        <div className="toolbar-right">
          <span className="stat-badge">{filteredNodes.length} nodes</span>
          <span className="stat-badge">{filteredEdges.length} edges</span>
        </div>
      </div>

      <div className="graph-container">
        <FilterPanel 
          filters={filters}
          onFilterChange={setFilters}
          nodeTypes={Array.from(new Set(nodes.map(n => n.type)))}
        />

        <div className="graph-main">
          {activeView === 'graph' && (
            <GraphVisualization 
              nodes={filteredNodes}
              edges={filteredEdges}
              onNodeClick={setSelectedNode}
              selectedNode={selectedNode}
            />
          )}

          {activeView === 'clusters' && (
            <div className="clusters-view">
              <div className="clusters-grid">
                {clusters.map(cluster => (
                  <div key={cluster.id} className="cluster-card">
                    <h3>{cluster.name}</h3>
                    <p className="cluster-topic">{cluster.primary_topic}</p>
                    <div className="cluster-stats">
                      <span>{cluster.size} concepts</span>
                      <span className="cohesion">Cohesion: {(cluster.cohesion * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeView === 'stats' && stats && (
            <div className="stats-view">
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Total Nodes</h3>
                  <p className="stat-value">{stats.total_nodes}</p>
                </div>
                <div className="stat-card">
                  <h3>Total Edges</h3>
                  <p className="stat-value">{stats.total_edges}</p>
                </div>
                <div className="stat-card">
                  <h3>Clusters</h3>
                  <p className="stat-value">{stats.total_clusters}</p>
                </div>
                <div className="stat-card">
                  <h3>Graph Density</h3>
                  <p className="stat-value">
                    {(stats.total_edges / (stats.total_nodes * (stats.total_nodes - 1))).toFixed(3)}
                  </p>
                </div>
              </div>

              <div className="node-types-section">
                <h3>Node Types Distribution</h3>
                <div className="type-list">
                  {Object.entries(stats.node_types || {}).map(([type, count]) => (
                    <div key={type} className="type-item">
                      <span className="type-name">{type}</span>
                      <div className="type-bar">
                        <div 
                          className="type-fill"
                          style={{ width: `${(count / stats.total_nodes) * 100}%` }}
                        ></div>
                      </div>
                      <span className="type-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="top-nodes-section">
                <h3>Top 10 Most Important Concepts</h3>
                <div className="top-nodes-list">
                  {stats.top_nodes?.map((node, idx) => (
                    <div key={idx} className="top-node-item">
                      <span className="rank">#{idx + 1}</span>
                      <span className="node-name">{node.name}</span>
                      <span className="node-type">{node.type}</span>
                      <span className="node-importance">
                        ⭐ {(node.importance * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {selectedNode && (
          <NodeDetailsPanel 
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>

      {recommendations.length > 0 && (
        <RecommendationPanel 
          recommendations={recommendations}
          title="Related Memories"
        />
      )}
    </div>
  );
}
