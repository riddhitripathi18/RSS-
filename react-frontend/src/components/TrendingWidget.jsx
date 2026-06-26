import React, { useEffect, useState } from 'react';

export default function TrendingWidget({ onArticleClick }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/trending')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch trending:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return null;
  if (!data || !data.overview) return null;

  // Parse the overview string into clickable list items
  const renderListItems = () => {
    const lines = data.overview.split('\n').filter(line => line.trim().length > 0);
    
    // Check if it looks like a numbered list
    const isNumberedList = lines.every(line => /^\d+\./.test(line.trim()));

    if (isNumberedList && data.articles && data.articles.length > 0) {
      return (
        <ol style={{ paddingLeft: '1.5rem', margin: 0 }}>
          {lines.map((line, idx) => {
            // Match pattern: "1. **Title** - Summary" or similar
            const match = line.trim().match(/^\d+\.\s*(?:\*\*)?(.*?)(?:\*\*)?\s*-\s*(.*)/);
            const article = data.articles[idx];

            if (match && article) {
              const title = match[1];
              const summary = match[2];
              return (
                <li key={idx} style={{ marginBottom: '12px', lineHeight: '1.6' }}>
                  <strong 
                    style={{ cursor: 'pointer', color: 'var(--primary)', textDecoration: 'none' }}
                    onClick={() => onArticleClick(article)}
                    onMouseEnter={e => e.target.style.textDecoration = 'underline'}
                    onMouseLeave={e => e.target.style.textDecoration = 'none'}
                  >
                    {title}
                  </strong>
                  {" - " + summary.replace(/\*\*/g, '')}
                </li>
              );
            } else if (article) {
               // Fallback if parsing fails but we have an article
               const cleanLine = line.replace(/^\d+\.\s*/, '').replace(/\*\*/g, '');
               return (
                 <li key={idx} style={{ marginBottom: '12px', lineHeight: '1.6' }}>
                   <strong 
                     style={{ cursor: 'pointer', color: 'var(--primary)' }}
                     onClick={() => onArticleClick(article)}
                     onMouseEnter={e => e.target.style.textDecoration = 'underline'}
                     onMouseLeave={e => e.target.style.textDecoration = 'none'}
                   >
                     {article.title}
                   </strong>
                   {" - " + cleanLine}
                 </li>
               );
            }
            // Absolute fallback
            return <li key={idx} style={{ marginBottom: '12px', lineHeight: '1.6' }}>{line}</li>;
          })}
        </ol>
      );
    }

    // If not a numbered list, fallback to standard HTML rendering
    let formatted = data.overview.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return <div dangerouslySetInnerHTML={{ __html: formatted }} />;
  };

  return (
    <div className="trending-widget" style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: '24px',
      marginBottom: '30px',
      boxShadow: 'var(--shadow-sm)'
    }}>
      <h4 style={{ 
        margin: '0 0 16px 0', 
        color: '#0f172a', 
        fontSize: '1.25rem', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px' 
      }}>
        Trending: Last 24 Hours Overview
      </h4>
      <div style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>
        {renderListItems()}
      </div>
    </div>
  );
}
