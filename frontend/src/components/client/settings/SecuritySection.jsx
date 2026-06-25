import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, KeyRound, Mail, ShieldCheck, Copy, Check } from "lucide-react";
import toast from "react-hot-toast";

import authService from "../../../services/authService";
import ConfirmModal from "../../shared/Modal/ConfirmModal";
import { formatDateTime } from "../../../utils/client/format";
import "./settings.css";

const SecuritySection = ({ profile, apiKey, onRegenerateKey }) => {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [sendingReset, setSendingReset] = useState(false);

  // ============================
  // 📋 COPY MASKED KEY
  // ============================
  const handleCopy = () => {
    if (!apiKey?.masked) return;
    navigator.clipboard.writeText(apiKey.masked);
    setCopied(true);
    toast.success("Copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  // ============================
  // 🔁 REGENERATE API KEY
  // ============================
  const handleRegenerate = async () => {
    setConfirmOpen(false);
    setRegenerating(true);

    try {
      await onRegenerateKey?.();
      toast.success("API key regenerated");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to regenerate key");
    } finally {
      setRegenerating(false);
    }
  };

  // ============================
  // 🔑 SEND PASSWORD RESET LINK
  // ============================
  const handleSendResetLink = async () => {
    if (!profile?.email) {
      toast.error("No email on file for this account");
      return;
    }

    setSendingReset(true);

    try {
      await authService.forgotPassword(profile.email);
      toast.success(`Reset link sent to ${profile.email}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send reset link");
    } finally {
      setSendingReset(false);
    }
  };

  return (
    <>
      {/* ============================
          🔑 API KEY
      ============================ */}
      <div className="settings-card">
        <h3>
          <KeyRound size={18} /> API Key
        </h3>

        <div className="settings-form">
          <div className="settings-key-row">
            <code className="settings-key-box">
              {apiKey?.masked || "No API key generated yet"}
            </code>

            <span
              className={`settings-badge ${
                apiKey?.is_active ? "settings-badge--active" : "settings-badge--inactive"
              }`}
            >
              {apiKey?.is_active ? "Active" : "Inactive"}
            </span>
          </div>

          {apiKey?.created_at && (
            <p className="settings-hint">
              Created {formatDateTime(apiKey.created_at)}
            </p>
          )}

          <div className="settings-actions">
            <button className="settings-btn-secondary" onClick={handleCopy} disabled={!apiKey?.masked}>
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? "Copied" : "Copy"}
            </button>

            <button
              className="settings-btn-danger"
              onClick={() => setConfirmOpen(true)}
              disabled={regenerating}
            >
              {regenerating ? (
                <>
                  <Loader2 className="spinner" size={16} />
                  Regenerating...
                </>
              ) : (
                "Regenerate Key"
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ============================
          📧 ACCOUNT EMAIL
      ============================ */}
      <div className="settings-card">
        <h3>
          <Mail size={18} /> Account Email
        </h3>

        <div className="settings-form">
          <div className="settings-group">
            <label>Current Email</label>
            <input type="email" value={profile?.email || ""} disabled className="input-disabled" />
          </div>

          <div className="settings-actions">
            <Link to="/change-email" className="settings-btn-secondary settings-link-btn">
              Change Email
            </Link>
          </div>
        </div>
      </div>

      {/* ============================
          🔒 PASSWORD
      ============================ */}
      <div className="settings-card">
        <h3>
          <ShieldCheck size={18} /> Password
        </h3>

        <div className="settings-form">
          <p className="settings-hint">
            We'll email you a secure link to reset your password.
          </p>

          <div className="settings-actions">
            <button className="settings-btn-secondary" onClick={handleSendResetLink} disabled={sendingReset}>
              {sendingReset ? (
                <>
                  <Loader2 className="spinner" size={16} />
                  Sending...
                </>
              ) : (
                "Send Password Reset Link"
              )}
            </button>
          </div>
        </div>
      </div>

      <ConfirmModal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleRegenerate}
        title="Regenerate API Key"
        message="This will invalidate your current key immediately. Any integrations using it will stop working until updated. Continue?"
      />
    </>
  );
};

export default SecuritySection;