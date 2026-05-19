import React, { useState, useEffect } from 'react';
import '../styles/recommendation-panel.css';

export default function RecommendationPanel({ recommendations, title = "Recommendations" }) {
  const [collapsed, setCollapsed] = useState(false);

  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  return (
    <div className={`recommendation-panel ${collapsed ? 'collapsed' : ''}`}>
      <div className="panel-header">
        <h3>{title}</h3>
        <div className="header-actions">
          <span className="count">{recommendations.length}</span>
          <button 
            className="collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? '▶' : '▼'}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="panel-content">
          <div className="recommendations-list">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-item">
                <div className="rec-rank">#{idx + 1}</div>
                
                <div className="rec-main">
                  <div className="rec-title">
                    {rec.title || rec.name}
                  </div>
                  
                  {rec.reasoning && (
                    <p className="rec-reasoning">
                      💡 {rec.reasoning}
                    </p>
                  )}
                  
                  {rec.score && (
                    <div className="rec-score">
                      <div className="score-bar">
                        <div 
                          className="score-fill"
                          style={{ width: `${Math.min(rec.score * 100, 100)}%` }}
                        ></div>
                      </div>
                      <span className="score-value">{(rec.score * 100).toFixed(0)}%</span>
                    </div>
                  )}

                  {rec.days_since_seen && (
                    <p className="rec-meta">
                      ⏱️ Last seen {rec.days_since_seen} days ago
                    </p>
                  )}

                  {rec.type && (
                    <span className="rec-type-badge">{rec.type}</span>
                  )}
                </div>

                <div className="rec-actions">
                  <button className="action-btn">Learn More</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
