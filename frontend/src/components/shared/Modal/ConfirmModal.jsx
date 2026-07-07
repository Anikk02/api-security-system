import React from 'react';
import './Modal.css';

function ConfirmModal({ open, onClose, onConfirm, title, message }) {
  if (!open) return null;

  return (
    <div className="modal-overlay">
      <div className="modal card">
        <h3>{title}</h3>
        <p>{message}</p>

        <div className="modal-actions">
          <button className="btn" onClick={onClose}>Cancel</button>
          <button className="btn danger" onClick={onConfirm}>Confirm</button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;