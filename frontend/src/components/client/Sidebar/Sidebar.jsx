// frontend/src/components/client/Sidebar/Sidebar.jsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  Settings, 
  Shield,
  Activity,
  KeyRound,
  X
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ isOpen, onClose }) => {
  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/logs', icon: FileText, label: 'Logs' },
    { path: '/users', icon: Users, label: 'Users' },
    { path: '/activity', icon: Activity, label: 'Activity' },
    { path: '/api-keys', icon: KeyRound, label: 'API Keys' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <>
      <div 
        className={`sidebar-overlay ${isOpen ? 'sidebar-overlay--open' : ''}`} 
        onClick={onClose} 
      />

      <aside className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar__header">
          <div className="sidebar__logo">
            <Shield size={24} className="sidebar__logo-icon" />
            <div className="sidebar__logo-text">
              <h2>TriAnSec</h2>
              <p>API Security Layer</p>
            </div>
          </div>

          <button className="sidebar__close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <nav className="sidebar__nav">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => 
                `sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`
              }
              onClick={() => {
                if (window.innerWidth <= 768) {
                  onClose();
                }
              }}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <p>TriAnSec v2.0 • Secure</p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;