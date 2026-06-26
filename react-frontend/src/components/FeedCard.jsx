import React from 'react';

// Helper to format text with bold and newlines
function formatText(text) {
  if (!text) return "";
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  return { __html: formatted };
}

export default function FeedCard({ article, onClick }) {
  const date = new Date(article.published_date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
  
  // Decide which text to show
  let displayText = article.five_ws_content || article.bullets_content || article.description || article.content.substring(0, 150) + "...";
  if (displayText && displayText.length > 250) {
    displayText = displayText.substring(0, 250) + "...";
  }

  return (
    <div className="article-card" onClick={() => onClick(article)}>
      <div className="card-source">{article.source}</div>
      <h3 className="card-title">{article.title}</h3>
      
      <div 
        className="card-summary formatted-content"
        dangerouslySetInnerHTML={formatText(displayText)}
      />
      
      <div className="card-footer">
        <span>{date}</span>
        <span>{article.click_count || 0} views</span>
      </div>
    </div>
  );
}
