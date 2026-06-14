import React from 'react';
import './IntegrationSection.css';

function IntegrationSection({ apiKey }) {
  return (
    <div className="card">
      <h2>🔌 Integration</h2>

      <p>Use the following header in your backend requests:</p>

      <pre className="code-block">
{`X-API-KEY: ${apiKey}`}
      </pre>

      <p className="note">
        JWT authentication is managed by your system.
      </p>
    </div>
  );
}

export default IntegrationSection;