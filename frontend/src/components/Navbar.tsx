// components/Navbar.tsx — Top navigation bar with dynamic visibility based on Auth state

import { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { TrendingUp, Menu, X, LogOut, LogIn } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { logout } from '../api/client';

const allLinks = [
  { to: '/',            label: 'Home',      protected: false },
  { to: '/forecast',    label: 'Forecast',  protected: true },
  { to: '/dashboard',   label: 'Dashboard', protected: true },
  { to: '/history',     label: 'History',   protected: true },
];

export default function Navbar() {
  const navigate                = useNavigate();
  const [open, setOpen]         = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { token, username, clearAuth } = useAppStore();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = () => {
    logout();
    clearAuth();
    navigate('/login');
  };

  const visibleLinks = allLinks.filter(l => !l.protected || Boolean(token));

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
      background: scrolled ? 'rgba(5,13,26,0.97)' : 'rgba(5,13,26,0.75)',
      backdropFilter: 'blur(20px)',
      borderBottom: `1px solid rgba(96,165,250,${scrolled ? 0.2 : 0.08})`,
      transition: 'all 0.3s',
    }}>
      <div className="container" style={{ display:'flex', alignItems:'center', height:'64px', gap:'1.5rem' }}>

        {/* Logo */}
        <NavLink to="/" style={{ display:'flex', alignItems:'center', gap:'0.5rem', textDecoration:'none', flexShrink:0, marginRight:'auto' }}>
          <div style={{ background:'linear-gradient(135deg,#3b82f6,#06b6d4)', borderRadius:'8px', padding:'6px', display:'flex' }}>
            <TrendingUp size={20} color="#fff" />
          </div>
          <span style={{ fontFamily:'var(--font-heading)', fontWeight:800, fontSize:'1.1rem', color:'#fff' }}>
            Retail<span style={{ color:'#60a5fa' }}>IQ</span>
          </span>
        </NavLink>

        {/* Desktop links */}
        <div style={{ display:'flex', gap:'0.25rem', alignItems:'center' }} className="desktop-nav">
          {visibleLinks.map(l => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'}
              style={({ isActive }) => ({
                padding:'0.4rem 0.9rem', borderRadius:'8px', fontSize:'0.88rem', fontWeight:500,
                color: isActive ? '#fff' : 'var(--color-text-muted)',
                background: isActive ? 'rgba(59,130,246,0.18)' : 'transparent',
                transition:'all 0.2s', textDecoration:'none',
              })}
            >{l.label}</NavLink>
          ))}

          {/* Logout or Login Button */}
          {token ? (
            <button
              onClick={handleLogout}
              className="btn btn-ghost"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.4rem 0.9rem', fontSize: '0.88rem', color: '#ef4444',
                marginLeft: '0.5rem', cursor: 'pointer'
              }}
              title={username ? `Logged in as ${username}` : 'Logout'}
            >
              <LogOut size={16} /> Logout
            </button>
          ) : (
            <NavLink
              to="/login"
              className="btn btn-outline"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                padding: '0.4rem 0.9rem', fontSize: '0.88rem', marginLeft: '0.5rem',
                textDecoration: 'none'
              }}
            >
              <LogIn size={16} /> Sign In
            </NavLink>
          )}
        </div>

        {/* Mobile hamburger */}
        <button className="btn btn-ghost" style={{ padding:'0.4rem', display:'none' }} onClick={() => setOpen(!open)} id="mobile-menu-btn">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div style={{ padding:'1rem 1.5rem', borderTop:'1px solid var(--color-border)', background:'rgba(5,13,26,0.98)' }}>
          {visibleLinks.map(l => (
            <NavLink key={l.to} to={l.to} onClick={() => setOpen(false)}
              style={{ display:'block', padding:'0.6rem 0', color:'var(--color-text-muted)', fontSize:'0.95rem', textDecoration:'none' }}
            >{l.label}</NavLink>
          ))}
          {token ? (
            <button
              onClick={() => { setOpen(false); handleLogout(); }}
              style={{ display:'block', width:'100%', textAlign:'left', padding:'0.6rem 0', color:'#ef4444', fontSize:'0.95rem', background:'none', border:'none', cursor:'pointer' }}
            >
              Logout
            </button>
          ) : (
            <NavLink to="/login" onClick={() => setOpen(false)} style={{ display:'block', padding:'0.6rem 0', color:'#60a5fa', fontSize:'0.95rem', textDecoration:'none' }}>
              Sign In
            </NavLink>
          )}
        </div>
      )}

      <style>{`
        @media (max-width: 900px) {
          .desktop-nav { display: none !important; }
          #mobile-menu-btn { display: flex !important; }
        }
      `}</style>
    </nav>
  );
}
