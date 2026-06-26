import React from 'react';

// Helper to format text with bold and newlines
function formatText(text) {
  if (!text) return "";
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  return { __html: formatted };
}

export default function ArticleDetail({ article, onBack }) {
  if (!article) return null;

  const date = new Date(article.published_date).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric'
  });

  const hasAISummary = article.five_ws_content || article.bullets_content;

  return (
    <div className="detail-view">
      <button className="back-button" onClick={onBack}>
        ← Back to Feed
      </button>
      
      <h1 className="detail-title">{article.title}</h1>
      
      <div className="detail-meta">
        <span>Source: {article.source}</span>
        <span>•</span>
        <span>Published: {date}</span>
      </div>

      {hasAISummary && (
        <div className="ai-summary">
          <h3>✨ AI Generated Summary</h3>
          <div 
            className="formatted-content"
            dangerouslySetInnerHTML={formatText(article.five_ws_content || article.bullets_content)}
          />
        </div>
      )}

      <div className="detail-content formatted-content">
        <p>{article.description}</p>
        <p>{article.content}</p>
      </div>

      <div style={{ textAlign: 'center', marginTop: '3rem' }}>
        <a href={article.url} target="_blank" rel="noopener noreferrer" className="read-original-btn">
          Read Original Article
        </a>
      </div>
    </div>
  );
}
