import React from 'react';

const CATEGORIES = [
  "All",
  "Politics",
  "Technology",
  "Sports",
  "International",
  "Media",
  "Stock Market"
];

export default function Sidebar({ activeCategory, onCategoryChange, onSearch }) {
  return (
    <aside className="sidebar">
      <h1 style={{ letterSpacing: '0.1em' }}>NEWS DIGEST</h1>
      
      <div className="category-list">
        {CATEGORIES.map(category => (
          <button
            key={category}
            className={`category-item ${activeCategory === category ? 'active' : ''}`}
            onClick={() => onCategoryChange(category)}
          >
            {category}
          </button>
        ))}
      </div>
    </aside>
  );
}
