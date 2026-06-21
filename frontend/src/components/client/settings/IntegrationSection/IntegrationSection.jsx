import React, { useState } from 'react';
import { Copy } from 'lucide-react';
import toast from 'react-hot-toast';

import './IntegrationSection.css';

function IntegrationSection({ apiKey }) {
  const [copied, setCopied] = useState(null);

  const safeKey = apiKey || "YOUR_API_KEY";

  const headerSnippet = `X-API-KEY: ${safeKey}`;

  const curlSnippet = `curl -X GET https://api.yourdomain.com/resource \\
  -H "X-API-KEY: ${safeKey}"`;

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    toast.success("Copied to clipboard");

    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <div className="card">
      <h2>🔌 Integration</h2>

      <p className="desc">
        Use your API key to authenticate requests from your backend.
      </p>

      {/* ============================
          🔑 Header Example
      ============================ */}
      <div className="integration-block">
        <div className="block-header">
          <span>Header</span>
          <button onClick={() => handleCopy(headerSnippet, "header")}>
            <Copy size={14} />
          </button>
        </div>

        <pre className="code-block">
{headerSnippet}
        </pre>
      </div>

      {/* ============================
          🚀 cURL Example
      ============================ */}
      <div className="integration-block">
        <div className="block-header">
          <span>cURL Example</span>
          <button onClick={() => handleCopy(curlSnippet, "curl")}>
            <Copy size={14} />
          </button>
        </div>

        <pre className="code-block">
{curlSnippet}
        </pre>
      </div>

      {/* ============================
          📝 Notes
      ============================ */}
      <p className="note">
        ⚠️ Keep your API key secret. Do not expose it in frontend applications.
      </p>
    </div>
  );
}

export default IntegrationSection;