import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Users, 
  Settings, 
  Shield,
  Activity,
  BarChart3,
  X
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ isOpen, onClose }) => {
  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/logs', icon: FileText, label: 'Logs' },
    { path: '/users', icon: Users, label: 'Users' },
    { path: '/activity', icon: Activity, label: 'Activity' },
    { path: '/usage', icon: BarChart3, label: 'Usage'},
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
            <Shield size={32} className="sidebar__logo-icon" />
            <div>
              <h2>TriAnSec</h2>
              <p>API Security Layer</p>
            </div>
          </div>

          <button className="sidebar__close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <nav className="sidebar__nav" aria-label="Main navigation">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}   // ✅ FIXED
              className={({ isActive }) => 
                `sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`
              }
              onClick={onClose}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;