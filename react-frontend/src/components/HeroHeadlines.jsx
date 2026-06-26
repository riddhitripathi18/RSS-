import React from 'react';

export default function HeroHeadlines({ articles, onClick }) {
  if (!articles || articles.length === 0) return null;

  // We want exactly 1 large, 1 medium, and up to 4 small items for the grid
  const largeArticle = articles[0];
  const mediumArticle = articles[1];
  const smallArticles = articles.slice(2, 6); // Up to 4

  return (
    <div className="hero-grid">
      {/* Large Left Card */}
      {largeArticle && (
        <div className="hero-card large" onClick={() => onClick(largeArticle)}>
          <div className="card-source" style={{ color: '#fed7aa' }}>{largeArticle.source}</div>
          <h2 className="card-title">{largeArticle.title}</h2>
          <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.95rem', lineHeight: '1.5' }}>
            {largeArticle.description && largeArticle.description.substring(0, 120)}...
          </div>
        </div>
      )}

      {/* Medium Center Card */}
      {mediumArticle && (
        <div className="hero-card medium" onClick={() => onClick(mediumArticle)}>
          <div className="card-source">{mediumArticle.source}</div>
          <h2 className="card-title">{mediumArticle.title}</h2>
          <div className="card-summary">
            {mediumArticle.description && mediumArticle.description.substring(0, 180)}...
          </div>
          <div style={{ marginTop: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {new Date(mediumArticle.published_date).toLocaleDateString()}
          </div>
        </div>
      )}

      {/* Small Right Stack */}
      <div style={{ display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border)', paddingLeft: '1.5rem' }}>
        <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Trending Now
        </h4>
        {smallArticles.map(article => (
          <div key={article.id} className="hero-card small" onClick={() => onClick(article)}>
            <div style={{ flex: 1 }}>
              <div className="card-source">{article.source}</div>
              <h3 className="card-title">{article.title}</h3>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
