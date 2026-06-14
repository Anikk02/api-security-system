import React, { useState, useEffect } from 'react';
import './ProfileSection.css';

function ProfileSection({ email, onSave }) {
  const [value, setValue] = useState(email);
  const [loading, setLoading] = useState(false);

  // sync when backend data loads
  useEffect(() => {
    setValue(email);
  }, [email]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await onSave(value);
      alert("Profile updated");
    } catch (err) {
      console.error(err);
      alert("Update failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>👤 Profile</h2>

      <div className="form-group">
        <label>Email</label>
        <input
          type="email"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </div>

      <button className="btn" onClick={handleSave} disabled={loading}>
        {loading ? 'Saving...' : 'Save Changes'}
      </button>
    </div>
  );
}

export default ProfileSection;