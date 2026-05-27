import React, { useState } from 'react';
import { Search, Shield, AlertTriangle, Clock, Ban } from 'lucide-react';
import './User.css';

const User = () => {
  const [selectedUser, setSelectedUser] = useState(null);
  
  const users = [
    { id: 'Bot-10554096', violations: 25, score: 0.88, status: 'blocked', ip: '192.168.1.1', lastSeen: new Date() },
    { id: 'Anon-44939162', violations: 18, score: 0.92, status: 'monitoring', ip: '192.168.1.2', lastSeen: new Date() },
    { id: 'user-johndoe@example.com', violations: 12, score: 0.79, status: 'warning', ip: '192.168.1.3', lastSeen: new Date() },
  ];
  
  return (
    <div className="user-page">
      <div className="user-page__header">
        <h1 className="user-page__title">User Management</h1>
        <div className="user-page__search">
          <Search size={18} />
          <input type="text" placeholder="Search users..." />
        </div>
      </div>
      
      <div className="user-page__content">
        <div className="user-page__list">
          {users.map((user) => (
            <div
              key={user.id}
              className={`user-card ${selectedUser?.id === user.id ? 'user-card--selected' : ''}`}
              onClick={() => setSelectedUser(user)}
            >
              <div className="user-card__header">
                <div className="user-card__icon">
                  <Shield size={20} />
                </div>
                <div className="user-card__info">
                  <div className="user-card__id">{user.id}</div>
                  <div className="user-card__ip">{user.ip}</div>
                </div>
              </div>
              <div className="user-card__stats">
                <div className="user-card__stat">
                  <AlertTriangle size={14} />
                  <span>{user.violations} violations</span>
                </div>
                <div className="user-card__stat">
                  <Clock size={14} />
                  <span>Score: {(user.score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className={`user-card__status user-card__status--${user.status}`}>
                {user.status}
              </div>
            </div>
          ))}
        </div>
        
        {selectedUser && (
          <div className="user-page__details">
            <div className="user-details">
              <h2 className="user-details__title">User Details</h2>
              <div className="user-details__content">
                <div className="user-details__field">
                  <label>User ID</label>
                  <p>{selectedUser.id}</p>
                </div>
                <div className="user-details__field">
                  <label>IP Address</label>
                  <p>{selectedUser.ip}</p>
                </div>
                <div className="user-details__field">
                  <label>Violations</label>
                  <p>{selectedUser.violations}</p>
                </div>
                <div className="user-details__field">
                  <label>Risk Score</label>
                  <div className="user-details__score">
                    <div className="user-details__score-bar">
                      <div style={{ width: `${selectedUser.score * 100}%` }} />
                    </div>
                    <span>{(selectedUser.score * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="user-details__actions">
                  <button className="user-details__btn user-details__btn--warn">
                    <AlertTriangle size={18} />
                    Send Warning
                  </button>
                  <button className="user-details__btn user-details__btn--block">
                    <Ban size={18} />
                    Block User
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default User;