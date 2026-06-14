import React, { useState } from 'react';
import ConfirmModal from '../../../shared/Modal/ConfirmModal';
import toast from 'react-hot-toast';

import './ApiKeySection.css';

function ApiKeySection({ apiKey, onRegenerate }) {
  const [copied, setCopied] = useState(false);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    toast.success("API key copied");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirm = async () => {
    setOpen(false);
    setLoading(true);

    try {
      const res = await onRegenerate();
      toast.success("API Key regenerated");

      // Optional: show once (you can remove later)
      console.log("New Key:", res.api_key);

    } catch (err) {
      console.error(err);
      toast.error("Failed to regenerate key");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>🔑 API Key</h2>

      <div className="api-key-box">
        <code>{apiKey}</code>
      </div>

      <div className="api-actions">
        <button className="btn" onClick={handleCopy}>
          {copied ? 'Copied' : 'Copy'}
        </button>

        <button
          className="btn danger"
          onClick={() => setOpen(true)}
          disabled={loading}
        >
          {loading ? 'Regenerating...' : 'Regenerate'}
        </button>
      </div>

      <ConfirmModal
        open={open}
        onClose={() => setOpen(false)}
        onConfirm={handleConfirm}
        title="Regenerate API Key"
        message="This will invalidate your current key. Continue?"
      />
    </div>
  );
}

export default ApiKeySection;