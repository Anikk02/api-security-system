import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import './ProfileSection.css';

function ProfileSection({ profile, onSave }) {
  const [email, setEmail] = useState(profile?.email || '');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setEmail(profile?.email || '');
  }, [profile]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await onSave(email);
      toast.success("Profile updated");
    } catch (err) {
      console.error(err);
      toast.error("Update failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card profile-card">
      <h2>👤 Profile</h2>

      {/* =========================
          Identity Info
      ========================= */}
      <div className="profile-info">
        <div className="profile-row">
          <span>Client ID</span>
          <strong>{profile?.id || "—"}</strong>
        </div>

        <div className="profile-row">
          <span>Status</span>
          <strong className={`status ${profile?.status === "active" ? "active" : "inactive"}`}>
            {profile?.status || "active"}
          </strong>
        </div>

        <div className="profile-row">
          <span>Created</span>
          <strong>
            {profile?.created_at
              ? new Date(profile.created_at).toLocaleDateString()
              : "—"}
          </strong>
        </div>
      </div>

      {/* =========================
          Editable Email
      ========================= */}
      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      {/* =========================
          Actions
      ========================= */}
      <button className="btn" onClick={handleSave} disabled={loading}>
        {loading ? "Saving..." : "Save Changes"}
      </button>
    </div>
  );
}

export default ProfileSection;