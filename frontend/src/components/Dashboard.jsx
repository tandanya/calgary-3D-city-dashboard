import React, { useState, useEffect, useCallback } from 'react';
import CityScene from './CityScene';
import QueryInput from './QueryInput';
import BuildingPopup from './BuildingPopup';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function Dashboard() {
  const [buildings, setBuildings] = useState([]);
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [highlightedIds, setHighlightedIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [queryResult, setQueryResult] = useState(null);

  // Fetch buildings on mount
  useEffect(() => {
    fetchBuildings();
  }, []);

  const fetchBuildings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/buildings`);
      if (response.data.success) {
        setBuildings(response.data.data);
        setError(null);
      } else {
        setError(response.data.error);
      }
    } catch (err) {
      setError('Failed to fetch property data. Make sure the backend is running.');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBuildingClick = useCallback((building) => {
    setSelectedBuilding(building);
  }, []);

  const handleQuery = async (query) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/query`, { query });
      
      if (response.data.success) {
        setHighlightedIds(response.data.matching_ids);
        setQueryResult({
          filter: response.data.filter,
          count: response.data.count
        });
        setError(null);
      } else {
        setError(response.data.error);
        setHighlightedIds([]);
      }
    } catch (err) {
      setError('Query failed. Please try again.');
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearHighlights = () => {
    setHighlightedIds([]);
    setQueryResult(null);
  };

  return (
    <div className="dashboard">
      <div className="sidebar">
        <QueryInput onQuery={handleQuery} loading={loading} />
        
        {queryResult && (
          <div className="query-result">
            <h3>Query Result</h3>
            <p>Found <strong>{queryResult.count}</strong> matching properties</p>
            <p className="filter-info">
              Filter: {queryResult.filter.attribute} {queryResult.filter.operator} {queryResult.filter.value}
            </p>
            <button onClick={clearHighlights} className="clear-btn">
              Clear Highlights
            </button>
          </div>
        )}
        
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        
        <div className="stats">
          <h3>Statistics</h3>
          <p>Total properties: {buildings.length}</p>
          <p>Highlighted: {highlightedIds.length}</p>
        </div>
      </div>
      
      <div className="scene-container">
        {loading && buildings.length === 0 ? (
          <div className="loading">Loading city data...</div>
        ) : (
          <CityScene
            buildings={buildings}
            highlightedIds={highlightedIds}
            onBuildingClick={handleBuildingClick}
          />
        )}
      </div>
      
      {selectedBuilding && (
        <BuildingPopup
          building={selectedBuilding}
          onClose={() => setSelectedBuilding(null)}
          isHighlighted={highlightedIds.includes(selectedBuilding.id)}
        />
      )}
    </div>
  );
}

export default Dashboard;