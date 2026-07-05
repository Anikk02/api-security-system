// frontend/src/pages/Auth/ResetPassword.jsx
import React, { useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { Lock, Loader2, ArrowRight, Shield, CheckCircle } from "lucide-react";
import BackgroundWrapper from "../../background/BackgroundWrapper";
import { useAuthActions } from "../../hooks/client/useAuthActions";
import toast from "react-hot-toast";
import "../../styles/auth.css";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [success, setSuccess] = useState(false);

  const navigate = useNavigate();

  const { resetPassword, loading } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!password) {
      toast.error("Please enter a new password");
      return;
    }

    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
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

  // Token missing case
  if (!token) {
    return (
      <BackgroundWrapper>
        <div className="auth-page">
          <div className="auth-card">
            <div className="auth-card__header">
              <div className="auth-logo">
                <Shield className="auth-logo__icon" size={36} />
                <span className="auth-logo__text">TriAnSec</span>
              </div>
              <h2 className="auth-card__title">Invalid Link</h2>
              <p className="auth-card__subtitle">
                This password reset link is invalid or has expired.
              </p>
            </div>
            <div className="auth-card__footer">
              <Link to="/forgot-password" className="auth-footer__link">
                Request a new reset link
              </Link>
            </div>
          </div>
        </div>
      </BackgroundWrapper>
    );
  }

  return (
    <BackgroundWrapper>
      <div className="auth-page">
        <div className="auth-card auth-card--reset">
          <div className="auth-card__header">
            <div className="auth-logo">
              <Shield className="auth-logo__icon" size={36} />
              <span className="auth-logo__text">TriAnSec</span>
            </div>

            {!success ? (
              <>
                <h2 className="auth-card__title">Reset Password</h2>
                <p className="auth-card__subtitle">Enter your new password</p>
              </>
            ) : (
              <>
                <CheckCircle size={40} className="success-icon" />
                <h2 className="auth-card__title">Password Updated</h2>
                <p className="auth-card__subtitle">You can now login with your new password</p>
              </>
            )}
          </div>

          {!success ? (
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="auth-form__group">
                <label className="auth-form__label" htmlFor="password">New Password</label>
                <div className="auth-form__input-wrapper">
                  <Lock className="auth-form__icon" size={18} />
                  <input
                    id="password"
                    type="password"
                    className="auth-form__input"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    required
                    minLength={8}
                  />
                </div>
                <span className="auth-form__hint">
                  Must be at least 8 characters
                </span>
              </div>

              <button type="submit" className="auth-btn" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="auth-btn__spinner" size={18} />
                    Updating...
                  </>
                ) : (
                  <>
                    Reset Password
                    <ArrowRight className="auth-btn__arrow" size={18} />
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
              <ArrowRight className="auth-btn__arrow" size={18} />
            </button>
          )}

          <div className="auth-card__footer">
            <p className="auth-footer__text">
              <Link to="/login" className="auth-footer__link">
                Back to Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    </BackgroundWrapper>
  );
};

export default ResetPassword;