// frontend/src/pages/Auth/ForgotPassword.jsx
import React, { useState } from "react";
import { Mail, Loader2, ArrowRight, Shield, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";
import BackgroundWrapper from "../../background/BackgroundWrapper";
import { useAuthActions } from "../../hooks/client/useAuthActions";
import toast from "react-hot-toast";
import "../../styles/auth.css";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState(false);

  const { forgotPassword, loading, error } = useAuthActions();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email) {
      toast.error("Please enter your email");
      return;
    }

    if (loading) return;

    try {
      await forgotPassword(email);
      setSuccess(true);
      toast.success("Reset link sent to your email");
    } catch (err) {
      toast.error(
        err?.response?.data?.detail || error || "Something went wrong"
      );
    }
  };

  return (
    <BackgroundWrapper>
      <div className="auth-page">
        <div className="auth-card auth-card--forgot">
          <div className="auth-card__header">
            <div className="auth-logo">
              <Shield className="auth-logo__icon" size={36} />
              <span className="auth-logo__text">TriAnSec</span>
            </div>

            {!success ? (
              <>
                <h2 className="auth-card__title">Forgot Password</h2>
                <p className="auth-card__subtitle">Enter your email to receive a reset link</p>
              </>
            ) : (
              <>
                <CheckCircle size={40} className="success-icon" />
                <h2 className="auth-card__title">Check Your Email</h2>
                <p className="auth-card__subtitle">
                  We've sent a password reset link to <b>{email}</b>
                </p>
              </>
            )}
          </div>

          {!success ? (
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="auth-form__group">
                <label className="auth-form__label" htmlFor="email">Email Address</label>
                <div className="auth-form__input-wrapper">
                  <Mail className="auth-form__icon" size={18} />
                  <input
                    id="email"
                    type="email"
                    className="auth-form__input"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                    required
                  />
                </div>
              </div>

              <button type="submit" className="auth-btn" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="auth-btn__spinner" size={18} />
                    Sending...
                  </>
                ) : (
                  <>
                    Send Reset Link
                    <ArrowRight className="auth-btn__arrow" size={18} />
                  </>
                )}
              </button>
            </form>
          ) : (
            <div className="auth-actions">
              <button
                className="auth-btn auth-btn--secondary"
                onClick={() => {
                  setSuccess(false);
                  setEmail("");
                }}
              >
                Resend Email
              </button>
            </div>
          )}

          <div className="auth-card__footer">
            <p className="auth-footer__text">
              Remember your password?{' '}
              <Link to="/login" className="auth-footer__link">
                Log In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </BackgroundWrapper>
  );
};

export default ForgotPassword;