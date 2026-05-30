import React, { useState, useEffect, useCallback } from 'react';
import { Search, Shield, AlertTriangle, Clock, Ban, RefreshCw } from 'lucide-react';
import { dashboardService } from '../../services/dashboardService';
import { userService } from '../../services/userService';
import toast from 'react-hot-toast';
import './User.css';

const User = () => {
  const [selectedUser, setSelectedUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [blockingInProgress, setBlockingInProgress] = useState(false);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dashboardService.getSuspiciousUsers(20);
      setUsers(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error(error);
      toast.error('Failed to load user data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    const interval = setInterval(fetchUsers, 15000);
    return () => clearInterval(interval);
  }, [fetchUsers]);

  const filteredUsers = users.filter(user =>
    user.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.ip.includes(searchTerm)
  );

  const getSmartFallback = (action) => {
    switch (action.action) {
      case 'allow':
        return 'Request allowed — no anomaly detected';
      case 'block':
        return 'User blocked due to repeated violations';
      case 'throttle':
        return 'Rate limit triggered due to high request frequency';
      case 'warn':
        return 'Suspicious behavior detected — warning issued';
      default:
        return 'Suspicious activity detected';
    }
  };

  const formatAction = (action) =>
    action ? action.charAt(0).toUpperCase() + action.slice(1) : "Unknown";

  const isUserBlocked = (user) => user?.isBlocked === true;

  // ================= ACTIONS =================

  const handleBlockUser = async (user) => {
    if (blockingInProgress) return;

    const toastId = toast.loading(`Blocking ${user.id}...`);
    setBlockingInProgress(true);

    try {
      const userId = user.id.replace('user-', '');

      const res = await fetch(`http://localhost:8000/api/dashboard/user/${userId}/block?duration=3600`, {
        method: 'POST'
      });

      const result = await res.json();

      if (result.success) {
        toast.success(`${user.id} blocked`, { id: toastId });
        await fetchUsers();
        setSelectedUser(prev => ({ ...prev, isBlocked: true }));
      } else {
        toast.error(result.error, { id: toastId });
      }
    } catch {
      toast.error('Block failed', { id: toastId });
    } finally {
      setBlockingInProgress(false);
    }
  };

  const handleUnblockUser = async (user) => {
    if (blockingInProgress) return;

    const toastId = toast.loading(`Unblocking ${user.id}...`);
    setBlockingInProgress(true);

    try {
      const userId = user.id.replace('user-', '');

      const res = await fetch(`http://localhost:8000/api/dashboard/user/${userId}/unblock`, {
        method: 'POST'
      });

      const result = await res.json();

      if (result.success) {
        toast.success(`${user.id} unblocked`, { id: toastId });
        await fetchUsers();
        setSelectedUser(prev => ({ ...prev, isBlocked: false }));
      } else {
        toast.error(result.error, { id: toastId });
      }
    } catch {
      toast.error('Unblock failed', { id: toastId });
    } finally {
      setBlockingInProgress(false);
    }
  };

  const handleSendWarning = async (user) => {
    const toastId = toast.loading(`Sending warning...`);

    try {
      const userId = user.id.replace('user-', '');

      const res = await fetch(
        `http://localhost:8000/api/dashboard/user/${userId}/warning?message=${encodeURIComponent(
          "Suspicious API usage detected"
        )}`,
        { method: 'POST' }
      );

      const result = await res.json();

      if (result.success) {
        toast.success('Warning sent', { id: toastId });
      } else {
        toast.error(result.error, { id: toastId });
      }
    } catch {
      toast.error('Warning failed', { id: toastId });
    }
  };

  return (
    <div className="user-page">

      <div className="user-page__header">
        <h1>User Management</h1>

        <div className="user-page__controls">
          <div className="user-page__search">
            <Search size={18} />
            <input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <button onClick={fetchUsers} disabled={loading}>
            <RefreshCw className={loading ? 'rotating' : ''} />
          </button>
        </div>
      </div>

      <div className="user-page__info">
        <span>{lastUpdated.toLocaleTimeString()}</span>
        <span>{users.length} users</span>
      </div>

      <div className="user-page__content">

        {/* USER LIST */}
        <div className="user-page__list">
          {loading ? (
            <div className="user-page__loading">
              <div className="user-page__loading-spinner"></div>
              <p>Loading users...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="user-page__empty">
              <p>No users found</p>
            </div>
          ) : (
            filteredUsers.map((user) => (
              <div
                key={user.id}
                className={`user-card ${
                  selectedUser?.id === user.id ? 'user-card--selected' : ''
                }`}
                onClick={async () => {
                  try {
                    const userId = user.id.replace('user-', '');
                    const details = await userService.getUserDetails(userId);
                    setSelectedUser({ ...user, ...details });
                  } catch {
                    toast.error('Failed to load user');
                  }
                }}
              >
                {/* HEADER */}
                <div className="user-card__header">
                  <div className="user-card__icon">
                    <Shield size={18} />
                  </div>

                  <div className="user-card__info">
                    <div className="user-card__id">{user.id}</div>
                    <div className="user-card__ip">{user.ip}</div>
                  </div>
                </div>

                {/* STATS */}
                  <div className="user-card__stats">
                    <div className="user-card__stat">
                      <AlertTriangle size={14} />
                      <span>{user.violations} violations</span>
                    </div>

                    <div className="user-card__stat">
                      <Clock size={14} />
                      <span>
                        Score: {(user.threatScore * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* STATUS */}
                  <div
                    className={`user-card__status user-card__status--${user.status}`}
                  >
                    {user.status}
                  </div>
                </div>
              ))
            )}
      </div>

        {/* USER DETAILS */}
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
                  <label>Total Requests</label>
                  <p>{selectedUser.totalRequests || '-'}</p>
                </div>

                <div className="user-details__field">
                  <label>Violations</label>
                  <p>{selectedUser.violations}</p>
                </div>

                <div className="user-details__field">
                  <label>Risk Score</label>
                  <div className="user-details__score">
                    <div className="user-details__score-bar">
                      <div style={{ width: `${(selectedUser.currentRiskScore || 0) * 100}%` }} />
                    </div>
                    <span>{((selectedUser.currentRiskScore || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="user-details__field">
                  <label>Last Seen</label>
                  <p>
                    {selectedUser.lastSeen
                      ? new Date(selectedUser.lastSeen).toLocaleString()
                      : 'N/A'}
                  </p>
                </div>

                {/* ✅ ACTION BUTTONS */}
                <div className="user-details__actions">
                  <button
                    className="user-details__btn user-details__btn--warn"
                    onClick={() => handleSendWarning(selectedUser)}
                    disabled={blockingInProgress}
                  >
                    <AlertTriangle size={18} />
                    Send Warning
                  </button>

                  {isUserBlocked(selectedUser) ? (
                    <button
                      className="user-details__btn user-details__btn--unblock"
                      onClick={() => handleUnblockUser(selectedUser)}
                      disabled={blockingInProgress}
                    >
                      <Ban size={18} />
                      Unblock User
                    </button>
                  ) : (
                    <button
                      className="user-details__btn user-details__btn--block"
                      onClick={() => handleBlockUser(selectedUser)}
                      disabled={blockingInProgress}
                    >
                      <Ban size={18} />
                      Block User
                    </button>
                  )}
                </div>

                {/* 🔥 IMPROVED RECENT ACTIVITY */}
                {selectedUser.recentActions?.length > 0 && (
                  <div className="user-details__activity">
                    <div className="user-details__activity-header-main">
                      <h3>Recent Activity</h3>
                      <span className="activity-count">
                        {selectedUser.recentActions.length} events
                      </span>
                    </div>

                    <div className="user-details__activity-list">
                      {selectedUser.recentActions.slice(0, 6).map((action, i) => {
                        const risk = action.risk_score || action.riskScore || 0;

                        return (
                          <div
                            key={i}
                            className={`user-details__activity-item ${
                              risk > 0.7
                                ? 'high-risk'
                                : risk > 0.4
                                ? 'medium-risk'
                                : 'low-risk'
                            }`}
                          >
                            {/* TOP ROW */}
                            <div className="activity-top">
                              <span className={`badge badge--${action.action?.toLowerCase()}`}>
                                {formatAction(action.action)}
                              </span>

                              <span className="activity-time">
                                {new Date(action.timestamp).toLocaleTimeString()}
                              </span>
                            </div>

                            {/* 🔥 MAIN INSIGHT */}
                            <div className="activity-main">
                              {action.explanation?.summary ||
                                getSmartFallback(action)}
                            </div>

                            {/* 🔥 FEATURE SIGNALS */}
                            {action.explanation?.details?.feature_contributions && (
                              <div className="activity-features">
                                {Object.entries(
                                  action.explanation.details.feature_contributions
                                )
                                  .sort((a, b) => b[1] - a[1])
                                  .slice(0, 3)
                                  .map(([k, v]) => (
                                    <span key={k}>
                                      {k}: {v.toFixed(2)}
                                    </span>
                                  ))}
                              </div>
                            )}

                            {/* 🔥 RISK BAR */}
                            <div className="activity-risk">
                              <div
                                className="activity-risk-bar"
                                style={{ width: `${risk * 100}%` }}
                              />
                              <span>{(risk * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                        );
                      })}
                    </div>
                  </div>
                )}

              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default User;