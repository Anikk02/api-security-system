import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, Building, Loader2, ArrowRight, Check, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';
import './Register.css';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  // Password rules validation for UI feedback
  const rules = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    digit: /\d/.test(password),
  };

  const isPasswordValid = Object.values(rules).every(Boolean);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    if (!isPasswordValid) {
      toast.error('Password does not meet complexity requirements');
      return;
    }

    setIsSubmitting(true);
    try {
      await register(email, password, companyName);
      toast.success('Registration successful! Please log in.');
      navigate('/login');
    } catch (error) {
      console.error(error);
      const errorMsg = error.response?.data?.detail || 'Registration failed. Try again.';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-glow" />
      <div className="auth-card">
        <div className="auth-card__header">
          <div className="auth-logo">
            <Shield className="auth-logo__icon" size={36} />
            <span className="auth-logo__text">TrianSec</span>
          </div>
          <h2 className="auth-card__title">Create Account</h2>
          <p className="auth-card__subtitle">Get started with AI-powered security middleware</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
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
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className="auth-form__group">
            <label className="auth-form__label" htmlFor="company">Company Name (Optional)</label>
            <div className="auth-form__input-wrapper">
              <Building className="auth-form__icon" size={18} />
              <input
                id="company"
                type="text"
                className="auth-form__input"
                placeholder="Acme Corp"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className="auth-form__group">
            <label className="auth-form__label" htmlFor="password">Password</label>
            <div className="auth-form__input-wrapper">
              <Lock className="auth-form__icon" size={18} />
              <input
                id="password"
                type="password"
                className="auth-form__input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isSubmitting}
              />
            </div>

            {/* Password Validation Rules UI */}
            {password && (
              <div className="password-rules">
                <div className={`password-rules__item ${rules.length ? 'valid' : 'invalid'}`}>
                  {rules.length ? <Check size={12} /> : <X size={12} />}
                  <span>At least 8 characters</span>
                </div>
                <div className={`password-rules__item ${rules.uppercase ? 'valid' : 'invalid'}`}>
                  {rules.uppercase ? <Check size={12} /> : <X size={12} />}
                  <span>At least 1 uppercase letter</span>
                </div>
                <div className={`password-rules__item ${rules.lowercase ? 'valid' : 'invalid'}`}>
                  {rules.lowercase ? <Check size={12} /> : <X size={12} />}
                  <span>At least 1 lowercase letter</span>
                </div>
                <div className={`password-rules__item ${rules.digit ? 'valid' : 'invalid'}`}>
                  {rules.digit ? <Check size={12} /> : <X size={12} />}
                  <span>At least 1 number</span>
                </div>
              </div>
            )}
          </div>

          <button type="submit" className="auth-btn" disabled={isSubmitting || (password && !isPasswordValid)}>
            {isSubmitting ? (
              <>
                <Loader2 className="auth-btn__spinner" size={18} />
                Creating account...
              </>
            ) : (
              <>
                Create Account
                <ArrowRight className="auth-btn__arrow" size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-card__footer">
          <p className="auth-footer__text">
            Already have an account?{' '}
            <Link to="/login" className="auth-footer__link">
              Log In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
