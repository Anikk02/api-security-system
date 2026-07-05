// frontend/src/background/GridOverlay.jsx
import React from 'react';
import '../styles/grid.css';

const GridOverlay = () => {
  return (
    <div className="grid-overlay">
      <svg className="grid-svg" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(0, 255, 136, 0.03)" strokeWidth="1" />
          </pattern>
          <pattern id="grid-dots" width="60" height="60" patternUnits="userSpaceOnUse">
            <circle cx="30" cy="30" r="1" fill="rgba(0, 255, 136, 0.05)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        <rect width="100%" height="100%" fill="url(#grid-dots)" />
      </svg>
    </div>
  );
};

export default GridOverlay;