
import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedItems, setExpandedItems] = useState({});

  const toggleExpand = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResults([]);

    if (!url || !query) {
      setError("Please provide both a website URL and a search query.");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url, query }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || "Something went wrong.");
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || "Failed to search. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Website Content Search</h1>
        <p className="subtitle">
          Search through website content with precision
        </p>
      </header>

      <main className="main">
        <section className="search-card">
          <form onSubmit={handleSubmit} className="search-form">
            <div className="input-group">
              <span className="input-icon">🌐</span>
              <input
                id="url"
                type="url"
                placeholder="https://smarter.codes"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="url-input"
              />
            </div>
            <div className="search-row">
              <div className="input-group search-input-group">
                <span className="input-icon">🔍</span>
                <input
                  id="query"
                  type="text"
                  placeholder="AI"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="query-input"
                />
              </div>
              <button type="submit" disabled={loading} className="search-button">
                {loading ? "Searching..." : "Search"}
              </button>
            </div>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="results-section">
          <h2 className="results-title">Search Results</h2>
          {loading && <p className="loading-text">Searching and indexing content...</p>}
          {!loading && results.length === 0 && !error && (
            <p className="placeholder">
              No results yet. Submit a URL and query to see matches here.
            </p>
          )}
          <div className="results-list">
            {results.map((item, index) => (
              <article key={index} className="result-item">
                <div className="result-content">
                  <div className="result-text">
                    {item.content}
                  </div>
                  <div className="result-meta">
                    <span className="result-path">Path: /home</span>
                  </div>
                  <button 
                    className="view-html-button"
                    onClick={() => toggleExpand(index)}
                  >
                    <span className="html-icon">&lt;/&gt;</span> View HTML {expandedItems[index] ? '▲' : '▼'}
                  </button>
                  {expandedItems[index] && (
                    <div className="html-preview">
                      <pre className="html-code">
                        <code>{item.content}</code>
                      </pre>
                    </div>
                  )}
                </div>
                <div className="match-badge">
                  {(item.score * 100).toFixed(0)}% match
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>Figure: Sample Demo</p>
      </footer>
    </div>
  );
}

export default App;
