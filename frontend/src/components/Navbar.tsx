// components/Navbar.tsx — Top navigation bar with direct link access (No Auth)

import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { TrendingUp, Menu, X } from 'lucide-react';

const allLinks = [
  { to: '/',            label: 'Home' },
  { to: '/forecast',    label: 'Forecast' },
  { to: '/dashboard',   label: 'Dashboard' },
  { to: '/history',     label: 'History' },
];

export default function Navbar() {
  const [open, setOpen]         = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

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
          {allLinks.map(l => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'}
               style={({ isActive }) => ({
                 padding:'0.4rem 0.9rem', borderRadius:'8px', fontSize:'0.88rem', fontWeight:500,
                 color: isActive ? '#fff' : 'var(--color-text-muted)',
                 background: isActive ? 'rgba(59,130,246,0.18)' : 'transparent',
                 transition:'all 0.2s', textDecoration:'none',
               })}
            >{l.label}</NavLink>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button className="btn btn-ghost" style={{ padding:'0.4rem', display:'none' }} onClick={() => setOpen(!open)} id="mobile-menu-btn">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div style={{ padding:'1rem 1.5rem', borderTop:'1px solid var(--color-border)', background:'rgba(5,13,26,0.98)' }}>
          {allLinks.map(l => (
            <NavLink key={l.to} to={l.to} onClick={() => setOpen(false)}
               style={{ display:'block', padding:'0.6rem 0', color:'var(--color-text-muted)', fontSize:'0.95rem', textDecoration:'none' }}
            >{l.label}</NavLink>
          ))}
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
