import React, { useState, useEffect } from 'react';
import '../styles/node-details.css';

export default function NodeDetailsPanel({ node, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedSections, setExpandedSections] = useState({
    incoming: true,
    outgoing: true,
    metadata: true
  });

  useEffect(() => {
    fetchNodeDetails();
  }, [node]);

  const fetchNodeDetails = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/graph/nodes/${node.id}`, {
        headers: { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` }
      });
      const data = await res.json();
      setDetails(data);
    } catch (error) {
      console.error('Error fetching node details:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (loading) {
    return (
      <div className="node-details-panel">
        <div className="panel-header">
          <h2>Node Details</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (!details) {
    return null;
  }

  return (
    <div className="node-details-panel">
      <div className="panel-header">
        <div className="header-content">
          <h2>{details.name}</h2>
          <span className="node-type-badge" style={{
            backgroundColor: getNodeColor(details.type)
          }}>
            {details.type}
          </span>
        </div>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      <div className="panel-content">
        {/* Description */}
        {details.description && (
          <div className="details-section">
            <h3>Description</h3>
            <p>{details.description.substring(0, 200)}{details.description.length > 200 ? '...' : ''}</p>
          </div>
        )}

        {/* Metrics */}
        <div className="details-section metrics">
          <h3>Metrics</h3>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Importance</span>
              <div className="metric-bar">
                <div 
                  className="metric-fill"
                  style={{ width: `${details.importance * 100}%` }}
                ></div>
              </div>
              <span className="metric-value">{(details.importance * 100).toFixed(1)}%</span>
            </div>

            <div className="metric-card">
              <span className="metric-label">Frequency</span>
              <span className="metric-value large">{details.frequency}</span>
            </div>

            <div className="metric-card">
              <span className="metric-label">Connections</span>
              <span className="metric-value large">
                {(details.incoming_edges?.length || 0) + (details.outgoing_edges?.length || 0)}
              </span>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="details-section">
          <h3>Timeline</h3>
          <div className="timeline-info">
            <p><strong>Created:</strong> {new Date(details.created_at).toLocaleDateString()}</p>
            <p><strong>Last Seen:</strong> {new Date(details.last_seen).toLocaleDateString()}</p>
          </div>
        </div>

        {/* Incoming Edges */}
        <div className="details-section edges-section">
          <h3 
            className="section-title"
            onClick={() => toggleSection('incoming')}
          >
            Related From {details.incoming_edges?.length || 0}
            <span className={`expand-icon ${expandedSections.incoming ? 'expanded' : ''}`}>▶</span>
          </h3>
          {expandedSections.incoming && (
            <div className="edges-list">
              {details.incoming_edges?.map((edge, idx) => (
                <div key={idx} className="edge-item">
                  <div className="edge-info">
                    <span className="relationship-type">{edge.relationship_type}</span>
                    <div className="strength-bar">
                      <div 
                        className="strength-fill"
                        style={{ width: `${edge.strength * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  <span className="strength-label">{(edge.strength * 100).toFixed(0)}%</span>
                </div>
              ))}
              {(!details.incoming_edges || details.incoming_edges.length === 0) && (
                <p className="no-edges">No incoming relationships</p>
              )}
            </div>
          )}
        </div>

        {/* Outgoing Edges */}
        <div className="details-section edges-section">
          <h3 
            className="section-title"
            onClick={() => toggleSection('outgoing')}
          >
            Relates To {details.outgoing_edges?.length || 0}
            <span className={`expand-icon ${expandedSections.outgoing ? 'expanded' : ''}`}>▶</span>
          </h3>
          {expandedSections.outgoing && (
            <div className="edges-list">
              {details.outgoing_edges?.map((edge, idx) => (
                <div key={idx} className="edge-item">
                  <div className="edge-info">
                    <span className="relationship-type">{edge.relationship_type}</span>
                    <div className="strength-bar">
                      <div 
                        className="strength-fill"
                        style={{ width: `${edge.strength * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  <span className="strength-label">{(edge.strength * 100).toFixed(0)}%</span>
                </div>
              ))}
              {(!details.outgoing_edges || details.outgoing_edges.length === 0) && (
                <p className="no-edges">No outgoing relationships</p>
              )}
            </div>
          )}
        </div>

        {/* Metadata */}
        {details.metadata && Object.keys(details.metadata).length > 0 && (
          <div className="details-section">
            <h3 
              className="section-title"
              onClick={() => toggleSection('metadata')}
            >
              Metadata
              <span className={`expand-icon ${expandedSections.metadata ? 'expanded' : ''}`}>▶</span>
            </h3>
            {expandedSections.metadata && (
              <div className="metadata-list">
                {Object.entries(details.metadata).map(([key, value]) => (
                  <div key={key} className="metadata-item">
                    <span className="metadata-key">{key}</span>
                    <span className="metadata-value">{String(value)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function getNodeColor(type) {
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
}
