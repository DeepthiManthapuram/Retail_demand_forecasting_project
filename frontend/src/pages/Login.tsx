// pages/Login.tsx — JWT authentication page (login + register toggle)

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Lock, User, Mail, Eye, EyeOff, CheckCircle } from 'lucide-react';
import { login, register } from '../api/client';
import { useAppStore } from '../store/useAppStore';

export default function Login() {
  const navigate = useNavigate();
  const setAuth  = useAppStore(s => s.setAuth);

  const [isRegister, setIsRegister] = useState(false);
  const [showPwd, setShowPwd]       = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [form, setForm] = useState({ username:'', email:'', password:'' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(''); setSuccessMsg('');
    try {
      if (isRegister) {
        await register({ username: form.username, email: form.email, password: form.password });
        setSuccessMsg('Account created successfully! Please sign in with your credentials.');
        setIsRegister(false);
        setForm(f => ({ ...f, password: '' })); // Keep username for quick login
      } else {
        const data = await login(form.username, form.password);
        setAuth(data.access_token, data.username, data.role);
        navigate('/forecast');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(ellipse 70% 60% at 50% -5%, rgba(59,130,246,0.18) 0%, transparent 75%), var(--color-bg)',
      paddingTop: '64px',
      paddingBottom: '2rem',
    }}>
      {/* Expanded & Enlarged Sign In / Register Box */}
      <div className="glass-card fade-in-up" style={{
        width: '100%',
        maxWidth: 520,
        padding: '3.2rem 2.8rem',
        margin: '1.5rem',
        borderRadius: '20px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(59, 130, 246, 0.1)',
        border: '1px solid rgba(96,165,250,0.18)'
      }}>

        {/* Logo & Heading */}
        <div style={{ textAlign: 'center', marginBottom: '2.25rem' }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: 'linear-gradient(135deg,#3b82f6,#06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
            boxShadow: '0 8px 20px rgba(59,130,246,0.3)'
          }}>
            <TrendingUp size={32} color="#fff" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.4rem', fontFamily: 'var(--font-heading)' }}>
            Retail<span style={{ color: '#60a5fa' }}>IQ</span>
          </h1>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.95rem' }}>
            {isRegister ? 'Create your new account' : 'Sign in to access your dashboard'}
          </p>
        </div>

        {successMsg && (
          <div className="alert alert-success" style={{
            marginBottom: '1.5rem',
            padding: '0.85rem 1rem',
            fontSize: '0.88rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#10b981',
            borderRadius: '10px'
          }}>
            <CheckCircle size={18} /> {successMsg}
          </div>
        )}

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '1.5rem', padding: '0.85rem 1rem', fontSize: '0.88rem', borderRadius: '10px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label className="label" style={{ fontSize: '0.85rem', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: 6 }}>
              <User size={14} color="#60a5fa" /> Username
            </label>
            <input
              id="username-input"
              type="text"
              className="input"
              required
              autoComplete="username"
              placeholder="Enter username"
              style={{ padding: '0.75rem 1rem', fontSize: '0.95rem', borderRadius: '10px' }}
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
            />
          </div>

          {isRegister && (
            <div>
              <label className="label" style={{ fontSize: '0.85rem', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Mail size={14} color="#60a5fa" /> Email Address
              </label>
              <input
                id="email-input"
                type="email"
                className="input"
                required
                autoComplete="email"
                placeholder="Enter email address"
                style={{ padding: '0.75rem 1rem', fontSize: '0.95rem', borderRadius: '10px' }}
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              />
            </div>
          )}

          <div>
            <label className="label" style={{ fontSize: '0.85rem', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Lock size={14} color="#60a5fa" /> Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="password-input"
                type={showPwd ? 'text' : 'password'}
                className="input"
                required
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                placeholder="Enter password"
                style={{ padding: '0.75rem 2.8rem 0.75rem 1rem', fontSize: '0.95rem', borderRadius: '10px' }}
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                style={{
                  position: 'absolute',
                  right: '0.85rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--color-text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Centered Submit Button */}
          <button
            id="auth-submit-btn"
            type="submit"
            className="btn btn-primary pulse-glow"
            style={{
              marginTop: '0.75rem',
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: '0.85rem 1.5rem',
              fontSize: '1rem',
              fontWeight: 600,
              borderRadius: '10px'
            }}
            disabled={loading}
          >
            <span style={{ display: 'inline-block', width: '100%', textAlign: 'center' }}>
              {loading ? 'Please wait…' : isRegister ? 'Create Account' : 'Sign In'}
            </span>
          </button>
        </form>

        {/* Register / Login Toggle */}
        <div style={{ textAlign: 'center', marginTop: '1.75rem', fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
          {isRegister ? 'Already have an account? ' : "Don't have an account? "}
          <button
            onClick={() => { setIsRegister(!isRegister); setError(''); setSuccessMsg(''); }}
            style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontWeight: 600, marginLeft: '4px' }}
          >
            {isRegister ? 'Sign In' : 'Register'}
          </button>
        </div>

      </div>
    </div>
  );
}
