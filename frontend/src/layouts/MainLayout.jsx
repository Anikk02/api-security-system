import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar/Navbar';
import Sidebar from '../components/Sidebar/Sidebar';
import MobileBottomNav from '../components/MobileBottomNav/MobileBottomNav';
import './MainLayout.css';

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="main-layout">
      <Navbar onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="main-layout__content">
        <div className="main-layout__container">
          <Outlet />
        </div>
      </main>
      <MobileBottomNav />
    </div>
  );
};

export default MainLayout;