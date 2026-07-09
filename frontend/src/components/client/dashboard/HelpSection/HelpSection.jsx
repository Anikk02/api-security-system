// src/components/client/dashboard/HelpSection/HelpSection.jsx
import React from 'react';
import './HelpSection.css';
import { Users, FileText, HelpCircle, ChevronRight } from 'lucide-react';

const HelpSection = () => {
  return (
    <div className="help-container">
      <div className="help-content">
        <h3 className="help-title">Help & Quick Actions</h3>
        <div className="help-actions">
          <button className="help-btn primary">
            <Users size={18} />
            View all suspicious users
            <ChevronRight size={16} />
          </button>
          <button className="help-btn">
            <FileText size={18} />
            View all decisions
            <ChevronRight size={16} />
          </button>
        </div>
        <div className="help-hint">
          <HelpCircle size={16} />
          <span>Need help? Contact support or check the documentation.</span>
        </div>
      </div>
    </div>
  );
};

export default HelpSection;