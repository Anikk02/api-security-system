import React, { useEffect, useState } from "react";
import { Loader2, CheckCircle, SlidersHorizontal } from "lucide-react";
import toast from "react-hot-toast";

import "./settings.css";

const STORAGE_KEY = "client_dashboard_preferences";

const DEFAULT_PREFERENCES = {
  highRiskAlerts: true,
  weeklyDigest: true,
  loginNotifications: false,
};

// ============================
// 💾 LOAD/SAVE (BROWSER-LOCAL)
// ============================
const loadPreferences = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) } : DEFAULT_PREFERENCES;
  } catch {
    return DEFAULT_PREFERENCES;
  }
};

const PreferencesSection = () => {
  const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // ============================
  // 🔄 LOAD PREFERENCES
  // ============================
  useEffect(() => {
    setPreferences(loadPreferences());
  }, []);

  const toggle = (key) => {
    setPreferences((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // ============================
  // 💾 SAVE PREFERENCES
  // ============================
  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      toast.success("Preferences saved");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      toast.error("Failed to save preferences");
    } finally {
      setSaving(false);
    }
  };

  const options = [
    {
      key: "highRiskAlerts",
      label: "High-risk threat alerts",
      hint: "Get an email when a critical risk score or violation is detected",
    },
    {
      key: "weeklyDigest",
      label: "Weekly security digest",
      hint: "A weekly summary of traffic, blocks, and top violators",
    },
    {
      key: "loginNotifications",
      label: "New login notifications",
      hint: "Get notified when your account is accessed from a new device",
    },
  ];

  return (
    <div className="settings-card">
      <h3>
        <SlidersHorizontal size={18} /> Preferences
      </h3>

      <div className="settings-form">
        {options.map(({ key, label, hint }) => (
          <div className="settings-toggle-row" key={key}>
            <div className="settings-toggle-text">
              <label>{label}</label>
              <p className="settings-hint">{hint}</p>
            </div>

            <button
              type="button"
              role="switch"
              aria-checked={preferences[key]}
              className={`settings-toggle ${preferences[key] ? "settings-toggle--on" : ""}`}
              onClick={() => toggle(key)}
            >
              <span className="settings-toggle-knob" />
            </button>
          </div>
        ))}

        <p className="settings-hint settings-hint--muted">
          Preferences are saved to this browser.
        </p>

        <div className="settings-actions">
          <button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="spinner" size={16} />
                Saving...
              </>
            ) : (
              "Save Preferences"
            )}
          </button>

          {success && (
            <span className="success-msg">
              <CheckCircle size={16} /> Saved
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default PreferencesSection;