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
import UsagePage from './pages/client/Usage/UsagePage';
import APIKeys from './pages/client/APIKeys/APIKeys';

// 🔐 Auth Pages
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import ForgotPassword from './pages/Auth/ForgotPassword';
import ResetPassword from './pages/Auth/ResetPassword';
import ChangeEmail from './pages/Auth/ChangeEmail';

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
      backgroundColor: '#0a0a0a',
      color: '#ffffff'
    }}
  >
    <div className="dashboard-loading__spinner"></div>
    <p style={{ marginTop: '16px', fontFamily: 'inherit' }}>
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

          {/* 🌐 PUBLIC ROUTES */}
          <Route element={<PublicRoute />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            {/* ✅ NEW */}
            <Route path="change-email" element={<ChangeEmail />} />
          </Route>

          {/* 🔒 PROTECTED ROUTES */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<MainLayout />}>

              <Route index element={<Dashboard />} />
              <Route path="logs" element={<Logs />} />
              <Route path="users" element={<Users />} />
              <Route path="activity" element={<ActivityPage />} />
              <Route path="api-keys" element={<APIKeys />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="usage" element={<UsagePage />} />

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