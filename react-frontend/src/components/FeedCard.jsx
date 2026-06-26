import React from 'react';

// Helper to format text with bold and newlines
function formatText(text) {
  if (!text) return "";
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  return { __html: formatted };
}

export default function FeedCard({ article, format, onClick }) {
  const date = new Date(article.published_date).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
  
  // Decide which text to show based on format
  let displayText = article.description || article.content.substring(0, 150) + "...";
  if (format === "Bullets" && article.bullets_content) {
    displayText = article.bullets_content;
  } else if (format === "5 Ws" && article.five_ws_content) {
    displayText = article.five_ws_content;
  } else if (format === "TL;DR" && article.content) {
    displayText = article.content;
  }

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
