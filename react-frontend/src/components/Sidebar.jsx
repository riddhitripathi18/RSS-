import React from 'react';

const CATEGORIES = [
  "All",
  "Technology",
  "Business",
  "World",
  "Science",
  "Health",
  "Entertainment",
  "Sports"
];

export default function Sidebar({ activeCategory, onCategoryChange, onSearch }) {
  return (
    <aside className="sidebar">
      <h1>📰 NewsDigest</h1>
      
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
