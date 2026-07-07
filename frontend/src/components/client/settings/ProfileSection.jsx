import React, { useEffect, useState } from "react";
import { Loader2, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";

import authService from "../../../services/authService";
import "./settings.css";

const ProfileSection = () => {
  const [profile, setProfile] = useState(null);
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // ============================
  // 🔄 LOAD PROFILE
  // ============================
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await authService.getMe();

        setProfile(data);
        setCompany(data.company_name || "");
        setEmail(data.email || "");
      } catch (err) {
        toast.error("Failed to load profile");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // ============================
  // 💾 UPDATE PROFILE
  // ============================
  const handleSave = async () => {
    if (!company.trim()) {
      toast.error("Company name cannot be empty");
      return;
    }

    setSaving(true);
    setSuccess(false);

    try {
      await authService.updateProfile({
        company_name: company,
      });

      toast.success("Profile updated");
      setSuccess(true);

      // remove success after 2s
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  // ============================
  // ⏳ LOADING STATE
  // ============================
  if (loading) {
    return (
      <div className="settings-card">
        <h3>👤 Profile</h3>
        <div className="settings-loading">
          <Loader2 className="spinner" size={18} />
          <span>Loading profile...</span>
        </div>
      </div>
    );
  }

  // ============================
  // 🎨 UI
  // ============================
  return (
    <div className="settings-card">
      <h3>👤 Profile</h3>

      <div className="settings-form">
        {/* EMAIL (READ ONLY) */}
        <div className="settings-group">
          <label>Email</label>
          <input
            type="email"
            value={email}
            disabled
            className="input-disabled"
          />
        </div>

        {/* COMPANY */}
        <div className="settings-group">
          <label>Company Name</label>
          <input
            type="text"
            placeholder="Enter company name"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            disabled={saving}
          />
        </div>

        {/* ACTION */}
        <div className="settings-actions">
          <button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="spinner" size={16} />
                Saving...
              </>
            ) : (
              "Save Changes"
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

export default ProfileSection;