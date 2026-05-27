import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Users, Activity, Settings } from 'lucide-react';
import './MobileBottomNav.css';

const MobileBottomNav = () => {
  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Home' },
    { path: '/logs', icon: FileText, label: 'Logs' },
    { path: '/users', icon: Users, label: 'Users' },
    { path: '/activity', icon: Activity, label: 'Activity' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <nav className="mobile-bottom-nav">
      {menuItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) => 
            `mobile-bottom-nav__item ${isActive ? 'mobile-bottom-nav__item--active' : ''}`
          }
        >
          <item.icon size={20} />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
};

export default MobileBottomNav;