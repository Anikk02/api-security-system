import React, { useState, useEffect } from 'react';
import { Key, Plus, Copy, Trash2, Eye, EyeOff, AlertTriangle, ShieldCheck } from 'lucide-react';
import apiKeyService from '../../services/apiKeyService';
import toast from 'react-hot-toast';
import './APIKeys.css';

const APIKeys = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState('');
  const [generating, setGenerating] = useState(false);
  const [newKeyData, setNewKeyData] = useState(null); // stores { key, name } on generation
  const [showConfirmDelete, setShowConfirmDelete] = useState(null); // stores key ID to delete
  const [deleting, setDeleting] = useState(false);

  const fetchKeys = async () => {
    try {
      setLoading(true);
      const data = await apiKeyService.getKeys();
      setKeys(data);
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
      toast.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!newKeyName.trim()) {
      toast.error('Key name is required');
      return;
    }
    try {
      setGenerating(true);
      const res = await apiKeyService.createKey(newKeyName.trim());
      setNewKeyData(res);
      setNewKeyName('');
      toast.success('API Key generated successfully');
      fetchKeys();
    } catch (error) {
      console.error('Failed to generate API key:', error);
      toast.error('Failed to generate API key');
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleStatus = async (keyId, currentStatus) => {
    try {
      const newStatus = !currentStatus;
      await apiKeyService.updateKeyStatus(keyId, newStatus);
      toast.success(`Key ${newStatus ? 'activated' : 'deactivated'}`);
      setKeys(prevKeys =>
        prevKeys.map(k => (k.id === keyId ? { ...k, is_active: newStatus } : k))
      );
    } catch (error) {
      console.error('Failed to toggle API key status:', error);
      toast.error('Failed to update key status');
    }
  };

  const handleDeleteClick = (keyId) => {
    setShowConfirmDelete(keyId);
  };

  const handleConfirmDelete = async () => {
    if (!showConfirmDelete) return;
    try {
      setDeleting(true);
      await apiKeyService.deleteKey(showConfirmDelete);
      toast.success('API Key revoked successfully');
      setKeys(prevKeys => prevKeys.filter(k => k.id !== showConfirmDelete));
      setShowConfirmDelete(null);
    } catch (error) {
      console.error('Failed to revoke API key:', error);
      toast.error('Failed to revoke API key');
    } finally {
      setDeleting(false);
    }
  };

  const copyToClipboard = (text, type = 'API Key') => {
    navigator.clipboard.writeText(text);
    toast.success(`${type} copied to clipboard`);
  };

  if (loading && keys.length === 0) {
    return (
      <div className="apikeys-page">
        <div className="apikeys-page__header">
          <h1 className="apikeys-page__title">Developer Portal</h1>
        </div>
        <div className="apikeys-loading">
          <div className="apikeys-loading__spinner"></div>
          <p>Loading application keys...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="apikeys-page">
      <div className="apikeys-page__header">
        <div>
          <h1 className="apikeys-page__title">Developer Keys</h1>
          <p className="apikeys-page__subtitle">Manage API keys to authenticate your client applications with the Security Engine.</p>
        </div>
      </div>

      <div className="apikeys-content">
        {/* Create Key Card */}
        <div className="apikeys-card create-key-card">
          <h3 className="apikeys-card__title">Create API Key</h3>
          <p className="apikeys-card__desc">Generate a new secret API key to authenticate requests from your client SDKs/servers.</p>
          <form className="create-key-form" onSubmit={handleCreateKey}>
            <input
              type="text"
              placeholder="e.g., Production Server Key"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              className="create-key-form__input"
              maxLength={100}
              disabled={generating}
            />
            <button type="submit" className="create-key-form__btn" disabled={generating}>
              <Plus size={18} />
              <span>{generating ? 'Generating...' : 'Generate Key'}</span>
            </button>
          </form>
        </div>

        {/* Keys List */}
        <div className="apikeys-card keys-list-card">
          <h3 className="apikeys-card__title">Active Keys</h3>
          <div className="keys-table-container">
            {keys.length === 0 ? (
              <div className="keys-empty-state">
                <Key size={48} className="keys-empty-state__icon" />
                <p className="keys-empty-state__text">No API keys found. Generate a key above to get started.</p>
              </div>
            ) : (
              <table className="keys-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Key Preview</th>
                    <th>Created</th>
                    <th>Last Used</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map((k) => (
                    <tr key={k.id}>
                      <td className="key-name-cell">{k.name}</td>
                      <td>
                        <div className="key-preview-badge">
                          <code>{k.key_preview}</code>
                          <button 
                            className="key-preview-copy"
                            onClick={() => copyToClipboard(k.key_preview, 'Preview key')}
                            title="Copy key preview"
                          >
                            <Copy size={14} />
                          </button>
                        </div>
                      </td>
                      <td>{new Date(k.created_at).toLocaleDateString()}</td>
                      <td>
                        {k.last_used_at 
                          ? new Date(k.last_used_at).toLocaleString() 
                          : <span className="key-never-used">Never used</span>
                        }
                      </td>
                      <td>
                        <label className="toggle-switch">
                          <input 
                            type="checkbox" 
                            checked={k.is_active} 
                            onChange={() => handleToggleStatus(k.id, k.is_active)}
                          />
                          <span className="toggle-slider"></span>
                        </label>
                      </td>
                      <td>
                        <button 
                          className="key-action-btn key-action-btn--delete"
                          onClick={() => handleDeleteClick(k.id)}
                          title="Revoke API Key"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {/* SUCCESS MODAL FOR GENERATED KEY */}
      {newKeyData && (
        <div className="apikeys-modal-overlay">
          <div className="apikeys-modal">
            <div className="apikeys-modal__header">
              <ShieldCheck className="apikeys-modal__icon apikeys-modal__icon--success" size={40} />
              <h2>API Key Generated</h2>
            </div>
            <div className="apikeys-modal__body">
              <p className="modal-warning">
                <AlertTriangle size={16} />
                <span>Make sure to copy your API key now. For security reasons, you won't be able to see it again.</span>
              </p>
              <div className="modal-key-display">
                <label className="modal-key-display__label">Key Name</label>
                <div className="modal-key-display__name">{newKeyData.name}</div>
                
                <label className="modal-key-display__label">API Key</label>
                <div className="modal-key-display__value-row">
                  <code className="modal-key-display__code">{newKeyData.key}</code>
                  <button 
                    className="modal-key-display__copy"
                    onClick={() => copyToClipboard(newKeyData.key, 'Full API Key')}
                  >
                    <Copy size={18} />
                    <span>Copy</span>
                  </button>
                </div>
              </div>
            </div>
            <div className="apikeys-modal__footer">
              <button 
                className="modal-close-btn"
                onClick={() => setNewKeyData(null)}
              >
                I have copied the key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONFIRM REVOCATION MODAL */}
      {showConfirmDelete && (
        <div className="apikeys-modal-overlay">
          <div className="apikeys-modal">
            <div className="apikeys-modal__header">
              <AlertTriangle className="apikeys-modal__icon apikeys-modal__icon--danger" size={40} />
              <h2>Revoke API Key?</h2>
            </div>
            <div className="apikeys-modal__body">
              <p>Are you sure you want to revoke this API key? Any applications currently using this key will fail to authenticate with the Security Engine immediately. This action cannot be undone.</p>
            </div>
            <div className="apikeys-modal__footer">
              <button 
                className="modal-cancel-btn" 
                onClick={() => setShowConfirmDelete(null)}
                disabled={deleting}
              >
                Cancel
              </button>
              <button 
                className="modal-danger-btn" 
                onClick={handleConfirmDelete}
                disabled={deleting}
              >
                {deleting ? 'Revoking...' : 'Revoke Key'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIKeys;
