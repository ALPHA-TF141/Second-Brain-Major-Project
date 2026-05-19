import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MiniMap,
  addEdge,
  Connection
} from 'reactflow';
import 'reactflow/dist/style.css';
import '../styles/graph-visualization.css';

// Node type styling
const getNodeColor = (type) => {
  const colors = {
    concept: '#3b82f6',
    technology: '#8b5cf6',
    framework: '#ec4899',
    language: '#f59e0b',
    memory: '#10b981',
    session: '#06b6d4',
    topic: '#6366f1',
  };
  return colors[type] || '#6b7280';
};

const NodeElement = ({ data, isSelected }) => {
  const color = getNodeColor(data.type);

  return (
    <div
      className={`custom-node ${isSelected ? 'selected' : ''}`}
      style={{
        backgroundColor: color,
        borderColor: isSelected ? '#fff' : color,
        borderWidth: isSelected ? 3 : 2
      }}
    >
      <div className="node-label">{data.label}</div>
      <div className="node-type">{data.type}</div>
      <div className="node-score">⭐ {(data.importance * 100).toFixed(0)}%</div>
    </div>
  );
};

export default function GraphVisualization({ nodes, edges, onNodeClick, selectedNode }) {
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState([]);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState([]);

  // Convert data to React Flow format
  useEffect(() => {
    const flowNodesData = nodes.map(node => ({
      id: String(node.id),
      data: {
        label: node.name.substring(0, 20) + (node.name.length > 20 ? '...' : ''),
        type: node.type,
        importance: node.importance,
        frequency: node.frequency,
        fullName: node.name
      },
      position: {
        x: Math.random() * 500,
        y: Math.random() * 500
      },
      type: 'custom',
      selected: selectedNode?.id === node.id,
      style: {
        background: getNodeColor(node.type),
        border: selectedNode?.id === node.id ? '3px solid white' : '2px solid ' + getNodeColor(node.type),
        borderRadius: '50%',
        width: 60 + node.frequency,
        height: 60 + node.frequency,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        color: 'white',
        fontWeight: 'bold',
        fontSize: '10px',
        padding: '4px',
        transition: 'all 0.2s ease'
      }
    }));

    const flowEdgesData = edges.map((edge, idx) => ({
      id: `e-${edge.id || idx}`,
      source: String(edge.source_id),
      target: String(edge.target_id),
      animated: edge.strength > 0.8,
      style: {
        strokeWidth: Math.max(1, edge.strength * 3),
        stroke: `rgba(100, 100, 100, ${edge.strength})`,
      },
      label: edge.relationship_type,
      labelStyle: { fontSize: 10, fontWeight: 'bold' }
    }));

    setFlowNodes(flowNodesData);
    setFlowEdges(flowEdgesData);
  }, [nodes, edges, selectedNode, setFlowNodes, setFlowEdges]);

  const handleNodeClick = (_, node) => {
    const originalNode = nodes.find(n => String(n.id) === node.id);
    if (originalNode) {
      onNodeClick(originalNode);
    }
  };

  const onConnect = useCallback((connection) => {
    // Prevent adding new edges
  }, []);

  return (
    <div className="graph-visualization">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        fitView
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            // Get color from node style
            if (node.data?.type) {
              return getNodeColor(node.data.type);
            }
            return '#6b7280';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>

      <div className="graph-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          {['concept', 'technology', 'framework', 'language', 'memory', 'session'].map(type => (
            <div key={type} className="legend-item">
              <div 
                className="legend-color"
                style={{ backgroundColor: getNodeColor(type) }}
              ></div>
              <span>{type}</span>
            </div>
          ))}
        </div>
      </div>

      {selectedNode && (
        <div className="graph-tooltip">
          <h4>{selectedNode.name}</h4>
          <p><strong>Type:</strong> {selectedNode.type}</p>
          <p><strong>Frequency:</strong> {selectedNode.frequency}</p>
          <p><strong>Importance:</strong> {(selectedNode.importance * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}
