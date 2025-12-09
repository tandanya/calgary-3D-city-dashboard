import React from 'react';

function BuildingPopup({ building, onClose, isHighlighted }) {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      maximumFractionDigits: 0
    }).format(value);
  };
  
  return (
    <div className="building-popup">
      <button className="close-btn" onClick={onClose}>×</button>
      
      <h2>
        {isHighlighted && <span className="highlight-badge">★ Match</span>}
        Property Details  
      </h2>
      
      <div className="popup-content">
        <div className="info-row">
          <span className="label">ID:</span>
          <span className="value">{building.id}</span>
        </div>
        
        <div className="info-row">
          <span className="label">Address:</span>
          <span className="value">{building.address}</span>
        </div>
        
        <div className="info-row">
          <span className="label">Type:</span>
          <span className="value type-badge" data-type={building.building_type}>
            {building.building_type}
          </span>
        </div>
        
        <div className="info-row">
          <span className="label">Zoning:</span>
          <span className="value">{building.zoning}</span>
        </div>
        
        <div className="info-row">
          <span className="label">Height (inferred based on value):</span>
          <span className="value">{building.height.toFixed(1)} ft</span>
        </div>
        
        <div className="info-row">
          <span className="label">Assessed Value:</span>
          <span className="value">{formatCurrency(building.assessed_value)}</span>
        </div>

        
        <div className="info-row">
          <span className="label">Coordinates:</span>
          <span className="value">
            {building.latitude.toFixed(6)}, {building.longitude.toFixed(6)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default BuildingPopup;