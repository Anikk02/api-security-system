import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Mail, Loader2, ArrowRight, Shield, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthActions } from "../../hooks/client/useAuthActions";
import "./ChangeEmail.css";

function ChangeEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState(false);

  const { changeEmail, confirmEmail, loading } = useAuthActions();
  const navigate = useNavigate();

  // ============================
  // 🔐 CONFIRM EMAIL (LINK FLOW)
  // ============================
  useEffect(() => {
    if (!token) return;

    const verify = async () => {
      try {
        await confirmEmail(token);
        setSuccess(true);
        toast.success("Email updated successfully!");
      } catch (err) {
        toast.error("Invalid or expired link");
      }
    };

    verify();
  }, [token]);

  // ============================
  // 📩 REQUEST EMAIL CHANGE
  // ============================
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email) {
      toast.error("Enter new email");
      return;
    }

    try {
      await changeEmail(email);
      toast.success("Verification link sent!");
      setSuccess(true);
    } catch (err) {
      // error handled in hook
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

          {/* ============================
              🔁 HEADER STATES
          ============================ */}
          {token ? (
            <>
              <h2>Confirm Email Change</h2>
              <p>Verifying your new email...</p>
            </>
          ) : !success ? (
            <>
              <h2>Change Email</h2>
              <p>Enter your new email</p>
            </>
          ) : (
            <>
              <CheckCircle size={40} className="success-icon" />
              <h2>Verification Sent</h2>
              <p>Check your new email for confirmation link</p>
            </>
          )}
        </div>

        {/* ============================
            📩 REQUEST FORM
        ============================ */}
        {!token && !success && (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="auth-form__group">
              <label>New Email</label>

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
                  Change Email
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
        )}

        {/* ============================
            🔐 CONFIRM STATE
        ============================ */}
        {token && loading && <p className="auth-message">Verifying...</p>}

        {token && success && (
          <button className="auth-btn" onClick={() => navigate("/")}>
            Go to Dashboard
          </button>
        )}
      </div>
    </div>
  );
}

export default ChangeEmail;