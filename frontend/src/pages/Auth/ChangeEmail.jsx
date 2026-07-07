// frontend/src/pages/Auth/ChangeEmail.jsx
import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { Mail, Loader2, ArrowRight, Shield, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthActions } from "../../hooks/client/useAuthActions";
import BackgroundWrapper from "../../background/BackgroundWrapper";
import "../../styles/auth.css";

const ChangeEmail = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [confirmSuccess, setConfirmSuccess] = useState(false);

  const { changeEmail, confirmEmail, loading, error } = useAuthActions();
  const navigate = useNavigate();

  // ============================
  // 🔐 CONFIRM EMAIL (LINK FLOW)
  // ============================
  useEffect(() => {
    if (!token) return;

    const verify = async () => {
      setVerifying(true);
      try {
        await confirmEmail(token);
        setConfirmSuccess(true);
        setSuccess(true);
        toast.success("Email updated successfully!");
      } catch (err) {
        const errorMsg = err?.response?.data?.detail || "Invalid or expired link";
        toast.error(errorMsg);
        setConfirmSuccess(false);
      } finally {
        setVerifying(false);
      }
    };

    verify();
  }, [token, confirmEmail]);

  // ============================
  // 📩 REQUEST EMAIL CHANGE
  // ============================
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email) {
      toast.error("Please enter your new email");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error("Please enter a valid email address");
      return;
    }

    try {
      await changeEmail(email);
      setSuccess(true);
      toast.success("Verification link sent to your new email!");
    } catch (err) {
      const errorMsg = err?.response?.data?.detail || "Failed to send verification";
      toast.error(errorMsg);
      setSuccess(false);
    }
  };

  // ============================
  // 🎨 RENDER
  // ============================
  return (
    <BackgroundWrapper>
      <div className="auth-page">
        <div className="auth-card auth-card--change-email">
          <div className="auth-card__header">
            <div className="auth-logo">
              <Shield className="auth-logo__icon" size={36} />
              <span className="auth-logo__text">TriAnSec</span>
            </div>

            {/* ============================
                🔁 HEADER STATES
            ============================ */}
            {token ? (
              // 🔐 Token verification state
              <>
                <h2 className="auth-card__title">Confirm Email Change</h2>
                <p className="auth-card__subtitle">
                  {verifying ? (
                    <span className="auth-status-text">Verifying your new email...</span>
                  ) : confirmSuccess ? (
                    <span className="auth-status-text success-text">
                      Email updated successfully!
                    </span>
                  ) : (
                    <span className="auth-status-text error-text">
                      Verification failed. Please try again.
                    </span>
                  )}
                </p>
              </>
            ) : !success ? (
              // 📩 Request form state
              <>
                <h2 className="auth-card__title">Change Email</h2>
                <p className="auth-card__subtitle">Enter your new email address</p>
              </>
            ) : (
              // ✅ Success state
              <>
                <CheckCircle size={40} className="success-icon" />
                <h2 className="auth-card__title">Verification Sent</h2>
                <p className="auth-card__subtitle">
                  Check your new email for the confirmation link
                </p>
              </>
            )}
          </div>

          {/* ============================
              📩 REQUEST FORM (No Token, Not Success)
          ============================ */}
          {!token && !success && (
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="auth-form__group">
                <label className="auth-form__label" htmlFor="new-email">
                  New Email Address
                </label>
                <div className="auth-form__input-wrapper">
                  <Mail className="auth-form__icon" size={18} />
                  <input
                    id="new-email"
                    type="email"
                    className="auth-form__input"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                    required
                    autoFocus
                  />
                </div>
                <span className="auth-form__hint">
                  A verification link will be sent to this address
                </span>
                {error && (
                  <span className="auth-form__error">{error}</span>
                )}
              </div>

              <button type="submit" className="auth-btn" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="auth-btn__spinner" size={18} />
                    Sending...
                  </>
                ) : (
                  <>
                    Change Email
                    <ArrowRight className="auth-btn__arrow" size={18} />
                  </>
                )}
              </button>
            </form>
          )}

          {/* ============================
              🔐 CONFIRM STATE (Loading)
          ============================ */}
          {token && verifying && (
            <div className="auth-loading-state">
              <Loader2 className="auth-btn__spinner" size={32} />
              <p className="auth-message">Verifying your email change...</p>
            </div>
          )}

          {/* ============================
              🔐 CONFIRM STATE (Error)
          ============================ */}
          {token && !verifying && !confirmSuccess && (
            <div className="auth-error-state">
              <div className="auth-error-icon">⚠️</div>
              <p className="auth-message error-text">
                This verification link is invalid or has expired.
              </p>
              <button
                className="auth-btn auth-btn--secondary"
                onClick={() => navigate("/settings")}
                style={{ marginTop: '12px' }}
              >
                Back to Settings
              </button>
            </div>
          )}

          {/* ============================
              ✅ SUCCESS STATES
          ============================ */}
          {token && confirmSuccess && (
            <button 
              className="auth-btn" 
              onClick={() => navigate("/")}
              style={{ marginTop: '20px' }}
            >
              Go to Dashboard
              <ArrowRight className="auth-btn__arrow" size={18} />
            </button>
          )}

          {!token && success && (
            <div className="auth-actions">
              <button
                className="auth-btn"
                onClick={() => navigate("/settings")}
              >
                Back to Settings
                <ArrowRight className="auth-btn__arrow" size={18} />
              </button>
            </div>
          )}

          {/* ============================
              🔙 FOOTER LINKS
          ============================ */}
          {!token && !success && (
            <div className="auth-card__footer">
              <p className="auth-footer__text">
                <Link to="/settings" className="auth-footer__link">
                  Return to Settings
                </Link>
              </p>
            </div>
          )}

          {token && confirmSuccess && (
            <div className="auth-card__footer">
              <p className="auth-footer__text">
                <Link to="/settings" className="auth-footer__link">
                  Return to Settings
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </BackgroundWrapper>
  );
};

export default ChangeEmail;