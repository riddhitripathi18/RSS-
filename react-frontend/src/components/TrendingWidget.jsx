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

  // Format the text if it contains bolding or newlines
  const formatText = (text) => {
    if (!text) return { __html: "" };
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return { __html: formatted };
  };

  return (
    <div className="trending-widget" style={{
      background: 'rgba(255,255,255,0.8)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: '24px',
      marginBottom: '30px',
      boxShadow: 'var(--shadow-sm)'
    }}>
      <h4 style={{ 
        margin: '0 0 16px 0', 
        color: 'var(--primary)', 
        fontSize: '1.25rem', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px' 
      }}>
        📈 Trending: Last 24 Hours Overview
      </h4>
      <div 
        className="formatted-content"
        dangerouslySetInnerHTML={formatText(data.overview)}
        style={{ fontSize: '0.95rem', lineHeight: '1.6', color: 'var(--text-main)' }}
      />
    </div>
  );
}
