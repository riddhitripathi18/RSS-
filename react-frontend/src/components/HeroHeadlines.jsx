import React from 'react';

export default function HeroHeadlines() {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      padding: '24px',
      marginBottom: '20px',
      boxShadow: 'var(--shadow-sm)'
    }}>
      <h2 style={{ fontSize: '2rem', marginBottom: '8px' }}>Headlines</h2>
      <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.95rem' }}>
        Stay informed with real time updates from trusted global news sources
      </p>
    </div>
  );
}
