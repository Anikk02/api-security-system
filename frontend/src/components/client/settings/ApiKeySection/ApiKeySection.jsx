import React, { useState } from 'react';
import ConfirmModal from '../../../shared/Modal/ConfirmModal';
import toast from 'react-hot-toast';
import { Copy, Eye, EyeOff } from 'lucide-react';

import './ApiKeySection.css';

function ApiKeySection({ apiKey, onRegenerate, createdAt, isActive = true }) {
  const [copied, setCopied] = useState(false);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [show, setShow] = useState(false);

  const safeKey = apiKey || "No API key available";

  const handleCopy = () => {
    if (!apiKey) return;

    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    toast.success("API key copied");

    setTimeout(() => setCopied(false), 1500);
  };

  const handleConfirm = async () => {
    setOpen(false);
    setLoading(true);

    try {
      const res = await onRegenerate();
      toast.success("API Key regenerated");
      console.log("New Key:", res?.api_key);
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

      {/* Meta Info */}
      <div className="api-meta">
        <span className={`status ${isActive ? "active" : "revoked"}`}>
          {isActive ? "🟢 Active" : "🔴 Revoked"}
        </span>

        {createdAt && (
          <span className="created-at">
            Created: {new Date(createdAt).toLocaleDateString()}
          </span>
        )}
      </div>

      {/* Key Display */}
      <div className="api-key-box">
        <code>
          {show ? safeKey : maskKey(safeKey)}
        </code>

        <div className="icon-actions">
          <button onClick={() => setShow(!show)}>
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>

          <button onClick={handleCopy}>
            <Copy size={16} className={copied ? "copied" : ""} />
          </button>
        </div>
      </div>

      {/* Regenerate */}
      <button
        className="btn danger"
        onClick={() => setOpen(true)}
        disabled={loading}
      >
        {loading ? 'Regenerating...' : '🔄 Regenerate API Key'}
      </button>

      {/* Confirm Modal */}
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

// 🔐 Mask helper
function maskKey(key) {
  if (!key || key === "No API key available") return key;

  const visible = 6;
  return key.slice(0, visible) + "****" + key.slice(-4);
}

export default ApiKeySection;