import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedItems, setExpandedItems] = useState({});

  const toggleExpand = (idx) => {
    setExpandedItems(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResults([]);

    // Basic validation
    if (!url || !query) {
      setError("Need both a URL and a search query!");
      return;
    }

    try {
      setLoading(true);
      
      const res = await fetch(`${API_BASE}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, query }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "Something went wrong");
      }

      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || "Search failed - try again?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Website Content Search</h1>
        <p className="subtitle">
          AI-powered semantic search for any website
        </p>
      </header>

      <main className="main">
        <section className="search-card">
          <form onSubmit={handleSubmit} className="search-form">
            <div className="input-group">
              <span className="input-icon">🌐</span>
              <input
                type="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="url-input"
              />
            </div>
            <div className="search-row">
              <div className="input-group search-input-group">
                <span className="input-icon">🔍</span>
                <input
                  type="text"
                  placeholder="What are you looking for?"
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
          <h2 className="results-title">Results</h2>
          {loading && <p className="loading-text">Fetching and analyzing content...</p>}
          {!loading && results.length === 0 && !error && (
            <p className="placeholder">
              Enter a URL and search query above to get started
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
                    <span className="html-icon">&lt;/&gt;</span> {expandedItems[index] ? 'Hide' : 'Show'} Content {expandedItems[index] ? '▲' : '▼'}
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
        <p>Semantic Search Demo</p>
      </footer>
    </div>
  );
}

export default App;
