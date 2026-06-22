import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, Loader2, ArrowRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
      toast.success('Successfully logged in!');
      navigate('/');
    } catch (error) {
      console.error(error);
      const errorMsg = error.response?.data?.detail || 'Invalid email or password';
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
          <h2 className="auth-card__title">Welcome Back</h2>
          <p className="auth-card__subtitle">Log in to manage your API security dashboard</p>
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
            <div className="auth-form__label-row">
              <label className="auth-form__label" htmlFor="password">Password</label>
              <a href="#" className="auth-form__forgot-link" onClick={(e) => {
                e.preventDefault();
                toast.success('Check development logs for password reset token.', { duration: 5000 });
              }}>
                Forgot password?
              </a>
            </div>
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
          </div>

          <button type="submit" className="auth-btn" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="auth-btn__spinner" size={18} />
                Logging in...
              </>
            ) : (
              <>
                Log In
                <ArrowRight className="auth-btn__arrow" size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-card__footer">
          <p className="auth-footer__text">
            Don't have an account?{' '}
            <Link to="/register" className="auth-footer__link">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
