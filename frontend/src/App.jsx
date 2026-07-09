// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

import MainLayout from './layouts/client/MainLayout';

import Dashboard from './pages/client/Dashboard/Dashboard';
import Logs from './pages/client/Logs/Logs';
import Users from './pages/client/User/User';
import SettingsPage from './pages/client/settings/SettingsPage';
import ActivityPage from './pages/client/activity/ActivityPage';
import APIKeys from './pages/client/APIKeys/APIKeys';

// 🔐 Auth Pages with Background
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import ForgotPassword from './pages/Auth/ForgotPassword';
import ResetPassword from './pages/Auth/ResetPassword';
import ChangeEmail from './pages/Auth/ChangeEmail';

// Import background styles
import './styles/background.css';
import './App.css';

const SessionLoading = () => (
  <div
    className="dashboard-loading"
    style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: '#0a0e1a',
      color: '#ffffff'
    }}
  >
    <div className="dashboard-loading__spinner"></div>
    <p style={{ marginTop: '16px', fontFamily: 'inherit', color: 'rgba(255,255,255,0.6)' }}>
      Loading account session...
    </p>
  </div>
);

// 🔒 Protected Routes
const ProtectedRoute = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <SessionLoading />;

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

// 🌐 Public Routes
const PublicRoute = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <SessionLoading />;

  return isAuthenticated ? <Navigate to="/" replace /> : <Outlet />;
};

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <Toaster
          position="top-right"
          reverseOrder={false}
          toastOptions={{
            duration: 3000,
            style: {
              background: 'rgba(10, 14, 26, 0.9)',
              color: '#ffffff',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(10px)',
              borderRadius: '8px',
            },
            success: {
              iconTheme: {
                primary: '#00ff88',
                secondary: '#0a0e1a',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#0a0e1a',
              },
            },
          }}
        />

        <Routes>
          {/* 🌐 PUBLIC ROUTES - With TriAnSec Background */}
          <Route element={<PublicRoute />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/change-email" element={<ChangeEmail />} />
          </Route>

          {/* 🔒 PROTECTED ROUTES - MainLayout with sidebar, no background */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="logs" element={<Logs />} />
              <Route path="users" element={<Users />} />
              <Route path="activity" element={<ActivityPage />} />
              <Route path="api-keys" element={<APIKeys />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>

          {/* 🔁 FALLBACK */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
};

export default App;