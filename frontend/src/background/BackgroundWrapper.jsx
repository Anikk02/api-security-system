// frontend/src/background/BackgroundWrapper.jsx
import React, { lazy, Suspense } from 'react';
import '../styles/background.css';

// Lazy load the SecurityBackground to improve initial load
const SecurityBackground = lazy(() => import('./SecurityBackground'));

const BackgroundWrapper = ({ children, showBackground = true }) => {
  return (
    <div className="auth-page-wrapper">
      {showBackground && (
        <Suspense fallback={<div className="background-loading" />}>
          <SecurityBackground />
        </Suspense>
      )}
      <div className="auth-content-overlay">
        {children}
      </div>
    </div>
  );
};

export default BackgroundWrapper;