import { useState } from "react";
import authService from "../../services/authService";

export const useAuthActions = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleError = (err, fallback) => {
    const msg = err.response?.data?.detail || fallback;
    setError(msg);
    throw err;
  };

  // ============================
  // 🔐 LOGIN
  // ============================
  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.login(email, password);
    } catch (err) {
      handleError(err, "Login failed");
    } finally {
      setLoading(false);
    }
  };

  // ============================
  // 🔐 REGISTER
  // ============================
  const register = async (email, password, companyName) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.register(email, password, companyName);
    } catch (err) {
      handleError(err, "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  // ============================
  // 🔁 FORGOT PASSWORD
  // ============================
  const forgotPassword = async (email) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.forgotPassword(email);
    } catch (err) {
      handleError(err, "Failed to send reset link");
    } finally {
      setLoading(false);
    }
  };

  // ============================
  // 🔁 RESET PASSWORD
  // ============================
  const resetPassword = async (token, newPassword) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.resetPassword(token, newPassword);
    } catch (err) {
      handleError(err, "Password reset failed");
    } finally {
      setLoading(false);
    }
  };

  // ============================
  // 📧 CHANGE EMAIL (REQUEST)
  // ============================
  const changeEmail = async (newEmail) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.changeEmail(newEmail);
    } catch (err) {
      handleError(err, "Failed to request email change");
    } finally {
      setLoading(false);
    }
  };

  // ============================
  // 📧 CONFIRM EMAIL
  // ============================
  const confirmEmail = async (token) => {
    setLoading(true);
    setError(null);
    try {
      return await authService.confirmEmail(token);
    } catch (err) {
      handleError(err, "Email confirmation failed");
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,

    login,
    register,
    forgotPassword,
    resetPassword,
    changeEmail,
    confirmEmail,
  };
};