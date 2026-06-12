import React from 'react';
import { Menu, Bell, User, Shield, Zap } from 'lucide-react';
import './Navbar.css';

const Navbar = ({ onMenuClick }) => {
  return (
    <nav className="navbar">
      <div className="navbar__left">
        <button className="navbar__menu-btn" onClick={onMenuClick}>
          <Menu size={24} />
        </button>
        <div className="navbar__logo">
          <Shield size={24} className="navbar__logo-icon" />
          <span className="navbar__logo-text">API Security</span>
          <span className="navbar__badge">AI-Powered</span>
        </div>
      </div>
      <div className="navbar__right">
        <div className="navbar__status">
          <Zap size={16} />
          <span>Live</span>
        </div>
        <button className="navbar__icon-btn">
          <Bell size={20} />
        </button>
        <button className="navbar__user">
          <User size={20} />
          <span className="navbar__user-name">Admin</span>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;