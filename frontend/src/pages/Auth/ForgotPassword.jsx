import React, { useState } from "react";
import { Mail, Loader2, ArrowRight, Shield, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthActions } from "../../hooks/client/useAuthActions";
import "./ForgotPassword.css";

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

    if (loading) return; // 🔒 prevent spam click

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
              <h2>Forgot Password</h2>
              <p>Enter your email to receive a reset link</p>
            </>
          ) : (
            <>
              <CheckCircle size={40} className="success-icon" />
              <h2>Check Your Email</h2>
              <p>
                We’ve sent a password reset link to <b>{email}</b>
              </p>
            </>
          )}
        </div>

        {/* ============================
            📩 FORM
        ============================ */}
        {!success ? (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="auth-form__group">
              <label>Email Address</label>

              <div className="auth-form__input-wrapper">
                <Mail size={18} />
                <input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <button className="auth-btn" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="spinner" size={18} />
                  Sending...
                </>
              ) : (
                <>
                  Send Reset Link
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
        ) : (
          // ✅ Better UX after success
          <div className="auth-actions">
            <button
              className="auth-btn secondary"
              onClick={() => {
                setSuccess(false);
                setEmail("");
              }}
            >
              Resend Email
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;