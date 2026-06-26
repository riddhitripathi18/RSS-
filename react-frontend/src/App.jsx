import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import FeedCard from './components/FeedCard';
import ArticleDetail from './components/ArticleDetail';
import './index.css';

const API_BASE_URL = 'http://localhost:8000/api/articles';

function App() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeArticle, setActiveArticle] = useState(null);

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

  const handleArticleClick = async (article) => {
    // Fetch full details (and trigger click_count increment)
    try {
      const response = await fetch(`${API_BASE_URL}/${article.id}`);
      const fullArticle = await response.json();
      setActiveArticle(fullArticle);
    } catch(err) {
      setActiveArticle(article); // fallback
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

            {loading ? (
              <p>Loading the latest news...</p>
            ) : articles.length > 0 ? (
              <div className="feed-grid">
                {articles.map(article => (
                  <FeedCard 
                    key={article.id} 
                    article={article} 
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
            onBack={() => setActiveArticle(null)} 
          />
        )}
      </main>
    </div>
  );
}

export default App;
