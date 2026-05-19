import React, { useState } from 'react';
import '../styles/filter-panel.css';

export default function FilterPanel({ filters, onFilterChange, nodeTypes }) {
  const [collapsed, setCollapsed] = useState(false);

  const handleTypeChange = (type) => {
    onFilterChange({
      ...filters,
      nodeType: filters.nodeType === type ? null : type
    });
  };

  const handleImportanceChange = (value) => {
    onFilterChange({
      ...filters,
      minImportance: parseFloat(value)
    });
  };

  const handleStrengthChange = (value) => {
    onFilterChange({
      ...filters,
      minStrength: parseFloat(value)
    });
  };

  const handleSearchChange = (value) => {
    onFilterChange({
      ...filters,
      searchQuery: value
    });
  };

  const handleReset = () => {
    onFilterChange({
      nodeType: null,
      minImportance: 0,
      minStrength: 0,
      searchQuery: ''
    });
  };

  return (
    <div className={`filter-panel ${collapsed ? 'collapsed' : ''}`}>
      <div className="filter-header">
        <h3>Filters</h3>
        <button 
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? '▶' : '▼'}
        </button>
      </div>

      {!collapsed && (
        <div className="filter-content">
          {/* Search */}
          <div className="filter-group">
            <label>Search</label>
            <input
              type="text"
              placeholder="Search nodes..."
              value={filters.searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="filter-input"
            />
          </div>

          {/* Node Type */}
          <div className="filter-group">
            <label>Node Type</label>
            <div className="filter-buttons">
              {nodeTypes.map(type => (
                <button
                  key={type}
                  className={`filter-btn ${filters.nodeType === type ? 'active' : ''}`}
                  onClick={() => handleTypeChange(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Importance Slider */}
          <div className="filter-group">
            <label>
              Min Importance: {(filters.minImportance * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.minImportance}
              onChange={(e) => handleImportanceChange(e.target.value)}
              className="filter-slider"
            />
          </div>

          {/* Strength Slider */}
          <div className="filter-group">
            <label>
              Min Relationship Strength: {(filters.minStrength * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={filters.minStrength}
              onChange={(e) => handleStrengthChange(e.target.value)}
              className="filter-slider"
            />
          </div>

          {/* Reset Button */}
          <button 
            onClick={handleReset}
            className="reset-btn"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}
