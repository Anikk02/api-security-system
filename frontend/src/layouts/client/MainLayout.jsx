// frontend/src/layouts/client/MainLayout.jsx
import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from '../../components/client/Navbar/Navbar';
import Sidebar from '../../components/client/Sidebar/Sidebar';
import MobileBottomNav from '../../components/client/MobileBottomNav/MobileBottomNav';
import './MainLayout.css';

const MainLayout = () => {
  // Get initial state from localStorage or default to true
  const getInitialSidebarState = () => {
    const saved = localStorage.getItem('sidebarOpen');
    if (saved !== null) {
      return JSON.parse(saved);
    }
    return true; // Default to open on desktop
  };

  const [sidebarOpen, setSidebarOpen] = useState(getInitialSidebarState);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  // Save sidebar state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('sidebarOpen', JSON.stringify(sidebarOpen));
  }, [sidebarOpen]);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
      } else {
        const saved = localStorage.getItem('sidebarOpen');
        if (saved !== null) {
          setSidebarOpen(JSON.parse(saved));
        } else {
          setSidebarOpen(true);
        }
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close sidebar on route change (mobile only)
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [location.pathname, isMobile]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="main-layout">
      <Navbar 
        onMenuClick={toggleSidebar} 
        isSidebarOpen={sidebarOpen && !isMobile} // Pass sidebar state to navbar
      />
      <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />
      <main className={`main-layout__content ${sidebarOpen && !isMobile ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="main-layout__container">
          <Outlet />
        </div>
      </main>
      <MobileBottomNav />
    </div>
  );
};

export default MainLayout;