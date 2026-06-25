import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Lock, Loader2, ArrowRight, Shield, CheckCircle } from "lucide-react";
import { useAuthActions } from "../../hooks/client/useAuthActions"; // ✅ use hook
import toast from "react-hot-toast";
import "./ResetPassword.css";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [success, setSuccess] = useState(false);

  const navigate = useNavigate();

  // ✅ Use centralized hook
  const { resetPassword, loading } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!password) {
      toast.error("Please enter a new password");
      return;
    }

    try {
      await resetPassword(token, password);

      setSuccess(true);
      toast.success("Password reset successful!");
    } catch (err) {
      toast.error(
        err.response?.data?.detail || "Reset failed"
      );
    }
  };

  // ❗ Token missing case
  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h2>Invalid or expired link</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-glow" />

      <div className="auth-card">
        <div className="auth-card__header">
          <div className="auth-logo">
            <Shield size={36} />
            <span>TriAnSec</span>
          </div>

          {!success ? (
            <>
              <h2>Reset Password</h2>
              <p>Enter your new password</p>
            </>
          ) : (
            <>
              <CheckCircle size={40} className="success-icon" />
              <h2>Password Updated</h2>
              <p>You can now login with your new password</p>
            </>
          )}
        </div>

        {!success ? (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="auth-form__group">
              <label>New Password</label>

              <div className="auth-form__input-wrapper">
                <Lock size={18} />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <button className="auth-btn" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="spinner" size={18} />
                  Updating...
                </>
              ) : (
                <>
                  Reset Password
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
        ) : (
          <button
            className="auth-btn"
            onClick={() => navigate("/login")}
          >
            Go to Login
          </button>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;