import React, { useState, useEffect, useCallback } from 'react';
import { Search, Shield, AlertTriangle, Clock, Ban, RefreshCw } from 'lucide-react';
import { dashboardService } from '../../services/dashboardService';
import toast from 'react-hot-toast';
import './User.css';

const User = () => {
  const [selectedUser, setSelectedUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [blockingInProgress, setBlockingInProgress] = useState(false);

  // Fetch users from backend
  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dashboardService.getSuspiciousUsers(20);
      setUsers(data);
      setLastUpdated(new Date());
      console.log('Users updated:', data.length, 'users found');
    } catch (error) {
      console.error('Failed to fetch users:', error);
      toast.error('Failed to load user data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Auto-refresh every 15 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchUsers();
    }, 15000);
    
    return () => clearInterval(interval);
  }, [fetchUsers]);

  // Filter users based on search
  const filteredUsers = users.filter(user => 
    user.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.ip.includes(searchTerm)
  );

  // Block user action - ACTUAL API CALL
  const handleBlockUser = async (user) => {
    if (blockingInProgress) return;
    
    const toastId = toast.loading(`Blocking ${user.id}...`);
    setBlockingInProgress(true);
    
    try {
      // Extract user ID from the display ID (format: "user-12345")
      const userId = user.id.replace('user-', '');
      
      // Call block API with 1 hour duration (3600 seconds)
      const response = await fetch(`http://localhost:8000/api/dashboard/user/${userId}/block?duration=3600`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`${user.id} has been blocked for 1 hour`, { id: toastId });
        // Refresh user list and selected user details
        await fetchUsers();
        // Update selected user block status
        if (selectedUser?.id === user.id) {
          setSelectedUser({ ...selectedUser, isBlocked: true });
        }
      } else {
        toast.error(`Failed to block ${user.id}: ${result.error}`, { id: toastId });
      }
    } catch (error) {
      console.error('Block error:', error);
      toast.error(`Failed to block ${user.id}. Make sure backend is running.`, { id: toastId });
    } finally {
      setBlockingInProgress(false);
    }
  };

  // Unblock user action
  const handleUnblockUser = async (user) => {
    if (blockingInProgress) return;
    
    const toastId = toast.loading(`Unblocking ${user.id}...`);
    setBlockingInProgress(true);
    
    try {
      const userId = user.id.replace('user-', '');
      
      const response = await fetch(`http://localhost:8000/api/dashboard/user/${userId}/unblock`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`${user.id} has been unblocked`, { id: toastId });
        await fetchUsers();
        if (selectedUser?.id === user.id) {
          setSelectedUser({ ...selectedUser, isBlocked: false });
        }
      } else {
        toast.error(`Failed to unblock ${user.id}: ${result.error}`, { id: toastId });
      }
    } catch (error) {
      console.error('Unblock error:', error);
      toast.error(`Failed to unblock ${user.id}`, { id: toastId });
    } finally {
      setBlockingInProgress(false);
    }
  };

  // Send warning action - ACTUAL API CALL
  const handleSendWarning = async (user) => {
    const toastId = toast.loading(`Sending warning to ${user.id}...`);
    
    try {
      const userId = user.id.replace('user-', '');
      const warningMessage = "Your API usage has been flagged as suspicious. Please review your integration to avoid being blocked.";
      
      const response = await fetch(`http://localhost:8000/api/dashboard/user/${userId}/warning?message=${encodeURIComponent(warningMessage)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Warning sent to ${user.id}`, { id: toastId });
        // Optional: Log warning in console for debugging
        console.log(`Warning sent to ${user.id}: ${warningMessage}`);
      } else {
        toast.error(`Failed to send warning: ${result.error}`, { id: toastId });
      }
    } catch (error) {
      console.error('Warning error:', error);
      toast.error(`Failed to send warning to ${user.id}. Make sure backend is running.`, { id: toastId });
    }
  };

  // Check if user is blocked (if we had that info from API)
  const isUserBlocked = (user) => {
    return user.isBlocked === true;
  };

  return (
    <div className="user-page">
      <div className="user-page__header">
        <h1 className="user-page__title">User Management</h1>
        <div className="user-page__controls">
          <div className="user-page__search">
            <Search size={18} />
            <input 
              type="text" 
              placeholder="Search users by ID or IP..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="user-page__refresh" onClick={fetchUsers} disabled={loading}>
            <RefreshCw size={18} className={loading ? 'rotating' : ''} />
            Refresh
          </button>
        </div>
      </div>
      
      <div className="user-page__info">
        <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
        <span>Total suspicious users: {users.length}</span>
      </div>
      
      <div className="user-page__content">
        <div className="user-page__list">
          {loading ? (
            <div className="user-page__loading">
              <div className="user-page__loading-spinner"></div>
              <p>Loading users...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="user-page__empty">
              <Shield size={48} />
              <p>No suspicious users found</p>
              <small>Run the attack simulation to generate data</small>
            </div>
          ) : (
            filteredUsers.map((user) => (
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
                    <span>Score: {(user.threatScore * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className={`user-card__status user-card__status--${user.status}`}>
                  {user.status}
                </div>
              </div>
            ))
          )}
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
                      <div style={{ width: `${selectedUser.threatScore * 100}%` }} />
                    </div>
                    <span>{(selectedUser.threatScore * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="user-details__field">
                  <label>Last Seen</label>
                  <p>{selectedUser.lastSeen ? new Date(selectedUser.lastSeen).toLocaleString() : 'N/A'}</p>
                </div>
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
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default User;