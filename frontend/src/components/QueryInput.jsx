import React, { useState } from 'react';

function QueryInput({ onQuery, loading }) {
  const [query, setQuery] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onQuery(query);
    }
  };
  
  const exampleQueries = [
    "Show properties over 100 feet",
    "Highlight commercial properties",
    "Show properties worth less than $50,000,000",
    "Find residential properties",
    "Show properties in R-CG zoning"
  ];
  
  return (
    <div className="query-input">
      <h3>🔍 Query properties</h3>
      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a query to highlight properties based on a filter."
          rows={3}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Processing...' : 'Search'}
        </button>
      </form>
      
      <div className="example-queries">
        <p>Try these examples:</p>
        <ul>
          {exampleQueries.map((eq, idx) => (
            <li key={idx}>
              <button 
                type="button"
                onClick={() => setQuery(eq)}
                className="example-btn"
              >
                {eq}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default QueryInput;