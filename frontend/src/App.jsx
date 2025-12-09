import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import './index.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Calgary 3D City Dashboard</h1>
        <p>Urban Design Visualization with AI-Powered Queries</p>
      </header>
      <Dashboard />
    </div>
  );
}

export default App;