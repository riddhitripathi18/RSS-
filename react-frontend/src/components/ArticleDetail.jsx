import React, { useState } from 'react';

function formatText(text) {
  if (!text) return "";
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  return { __html: formatted };
}

export default function ArticleDetail({ article, format, onFormatChange, onBack }) {
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  if (!article) return null;

  const date = new Date(article.published_date).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric'
  });

  const hasAISummary = article.five_ws_content || article.bullets_content || article.content;
  
  let displayText = article.description || "";
  if (format === "Bullets" && article.bullets_content) displayText = article.bullets_content;
  else if (format === "5 Ws" && article.five_ws_content) displayText = article.five_ws_content;
  else if (format === "TL;DR" && article.content) displayText = article.content;

  const loadAudio = async () => {
    setAudioLoading(true);
    try {
      const url = `http://localhost:8000/api/audio/${article.id}?format=${format}`;
      setAudioUrl(url);
    } catch (e) {
      console.error(e);
    } finally {
      setAudioLoading(false);
    }
  };

  return (
    <div className="detail-view">
      <button className="back-button" onClick={onBack}>
        ← Back to Feed
      </button>
      
      <h1 className="detail-title">{article.title}</h1>
      
      <div className="detail-meta">
        <span>Source: <strong>{article.source}</strong></span>
        <span>•</span>
        <span>Published: {date}</span>
        <span>•</span>
        <span>{article.click_count || 0} views</span>
      </div>

      {/* Format Switcher */}
      <div style={{ marginBottom: '20px' }}>
        <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, margin: '0 0 10px 0' }}>📄 Perspective Mode</p>
        <div style={{ display: 'flex', gap: '10px' }}>
          {['TL;DR', 'Bullets', '5 Ws'].map(f => (
            <button 
              key={f}
              onClick={() => {
                onFormatChange(f);
                setAudioUrl(null); // Reset audio if format changes
              }}
              style={{
                padding: '8px 16px', borderRadius: 'var(--radius-md)',
                backgroundColor: format === f ? 'var(--primary)' : 'var(--surface)',
                color: format === f ? 'white' : 'var(--text-main)',
                border: `1px solid ${format === f ? 'var(--primary)' : 'var(--border)'}`,
                cursor: 'pointer', fontWeight: 600, transition: 'var(--transition)'
              }}
            >
              {f === 'Bullets' ? '⚡ Key Takeaways' : f === '5 Ws' ? '❓ 5 Ws Analysis' : '📄 TL;DR Summary'}
            </button>
          ))}
        </div>
      </div>

      {/* Audio Player */}
      <div style={{ marginBottom: '2rem', padding: '16px', backgroundColor: '#1e293b', borderRadius: 'var(--radius-md)', color: 'white', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ width: '50px', height: '50px', borderRadius: '25px', backgroundColor: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 800 }}>
          AI
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: '0 0 4px 0', color: 'white', fontFamily: 'Inter' }}>Read with AI</h4>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>Listen to the {format} summary</p>
        </div>
        <div>
          {!audioUrl ? (
            <button onClick={loadAudio} disabled={audioLoading} style={{ padding: '8px 16px', borderRadius: '999px', backgroundColor: 'white', color: 'var(--primary)', border: 'none', cursor: 'pointer', fontWeight: 700 }}>
              {audioLoading ? "Generating..." : "▶ Play Audio"}
            </button>
          ) : (
            <audio controls autoPlay src={audioUrl} style={{ height: '40px' }} />
          )}
        </div>
      </div>

      {hasAISummary && (
        <div className="ai-summary">
          <h3>✨ AI Generated Content ({format})</h3>
          <div 
            className="formatted-content"
            style={{ whiteSpace: 'pre-line', lineHeight: '1.6' }}
            dangerouslySetInnerHTML={formatText(displayText)}
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
