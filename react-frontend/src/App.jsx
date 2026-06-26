import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import FeedCard from './components/FeedCard';
import ArticleDetail from './components/ArticleDetail';
import ChatBot from './components/ChatBot';
import TrendingWidget from './components/TrendingWidget';
import './index.css';

const API_BASE_URL = 'http://localhost:8000/api/articles';

function App() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeArticle, setActiveArticle] = useState(null);
  const [summaryFormat, setSummaryFormat] = useState('TL;DR');

  // Fetch articles from API
  const fetchArticles = async (category, query = '') => {
    setLoading(true);
    try {
      let url;
      let searchTerm = query;
      
      if (!searchTerm && category !== 'All') {
        searchTerm = category;
      }

      if (searchTerm) {
        url = `${API_BASE_URL}/search?keyword=${encodeURIComponent(searchTerm)}&limit=30`;
      } else {
        url = `${API_BASE_URL}/recent?limit=30`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setArticles(data || []);
    } catch (error) {
      console.error("Failed to fetch articles:", error);
    } finally {
      setLoading(false);
    }
  };

  // Run on mount and when category changes
  useEffect(() => {
    fetchArticles(activeCategory, searchQuery);
  }, [activeCategory]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchArticles(activeCategory, searchQuery);
  };

  const loadFormattedArticle = async (article, format) => {
    try {
      const res = await fetch('http://localhost:8000/api/articles/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: article.id, format: format })
      });
      const data = await res.json();
      return data;
    } catch(err) {
      console.error(err);
      return article;
    }
  };

  const handleArticleClick = async (article) => {
    const formatted = await loadFormattedArticle(article, summaryFormat);
    setActiveArticle(formatted);
  };

  const handleFormatChange = async (format) => {
    setSummaryFormat(format);
    if (activeArticle) {
      const formatted = await loadFormattedArticle(activeArticle, format);
      setActiveArticle(formatted);
    }
  };

  return (
    <div className="app-container">
      <Sidebar 
        activeCategory={activeCategory} 
        onCategoryChange={(cat) => {
          setActiveCategory(cat);
          setSearchQuery('');
          setActiveArticle(null);
        }} 
      />
      
      <main className="main-content">
        {!activeArticle ? (
          <>
            <div className="top-bar">
              <h2 className="page-title">{searchQuery ? `Results for "${searchQuery}"` : `${activeCategory} News`}</h2>
              
              <form onSubmit={handleSearch}>
                <input 
                  type="text" 
                  className="search-input" 
                  placeholder="Search articles..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </form>
            </div>

            {/* Trending Overview */}
            {activeCategory === 'All' && !searchQuery && (
              <TrendingWidget onArticleClick={handleArticleClick} />
            )}

            {/* Format Selection for Feed */}
            <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>📄 Perspective Mode:</span>
              {['TL;DR', 'Bullets', '5 Ws'].map(f => (
                <button 
                  key={f}
                  onClick={() => handleFormatChange(f)}
                  style={{
                    padding: '6px 12px', borderRadius: 'var(--radius-md)', fontSize: '0.85rem',
                    backgroundColor: summaryFormat === f ? 'var(--primary)' : 'var(--surface)',
                    color: summaryFormat === f ? 'white' : 'var(--text-main)',
                    border: `1px solid ${summaryFormat === f ? 'var(--primary)' : 'var(--border)'}`,
                    cursor: 'pointer', fontWeight: 600, transition: 'var(--transition)'
                  }}
                >
                  {f === 'Bullets' ? '⚡ Key Takeaways' : f === '5 Ws' ? '❓ 5 Ws Analysis' : '📄 TL;DR Summary'}
                </button>
              ))}
            </div>

            {loading ? (
              <p>Loading the latest news...</p>
            ) : articles.length > 0 ? (
              <div className="feed-grid">
                {articles.map(article => (
                  <FeedCard 
                    key={article.id} 
                    article={article} 
                    format={summaryFormat}
                    onClick={handleArticleClick}
                  />
                ))}
              </div>
            ) : (
              <p>No articles found for this category or search.</p>
            )}
          </>
        ) : (
          <ArticleDetail 
            article={activeArticle} 
            format={summaryFormat}
            onFormatChange={handleFormatChange}
            onBack={() => setActiveArticle(null)} 
          />
        )}
      </main>

      {/* Floating Chatbot */}
      <ChatBot activeArticle={activeArticle} />
    </div>
  );
}

export default App;
