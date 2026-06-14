import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import MainLayout from './layouts/client/MainLayout';

import Dashboard from './pages/client/Dashboard/Dashboard';
import Logs from './pages/client/Logs/Logs';
import User from './pages/client/User/User';
import SettingsPage from './pages/client/settings/SettingsPage';
import './App.css';

const App = () => {
  return (
    <Router>
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          duration: 3000,
          style: {
            background: '#1e1e1e',
            color: '#ffffff',
            border: '1px solid #2a2a2a',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
        }}
      />
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="logs" element={<Logs />} />
          <Route path="users" element={<User />} />
          <Route path="activity" element={<Dashboard />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback Route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;