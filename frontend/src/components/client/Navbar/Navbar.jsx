// frontend/src/components/client/Navbar/Navbar.jsx
import React from 'react';
import { Menu, Bell, User, Shield, Zap, LogOut } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import './Navbar.css';

const Navbar = ({ onMenuClick, isSidebarOpen }) => {
  const { user, logout } = useAuth();
  const displayName = user?.company_name || user?.email || 'Account';

  return (
    <nav className={`navbar ${isSidebarOpen ? 'navbar--sidebar-open' : 'navbar--sidebar-closed'}`}>
      <div className="navbar__left">
        <button className="navbar__menu-btn" onClick={onMenuClick}>
          <Menu size={24} />
        </button>
        <div className="navbar__logo">
          <Shield size={24} className="navbar__logo-icon" />
          <span className="navbar__logo-text">TriAnSec</span>
          <span className="navbar__badge">Behavior-based Middleware</span>
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
        <button className="navbar__user" title={displayName}>
          <User size={20} />
          <span className="navbar__user-name">{displayName}</span>
        </button>
        <button className="navbar__icon-btn" onClick={logout} title="Log out">
          <LogOut size={20} />
        </button>
      </div>
    </nav>
  );
};

export default Navbar;