// components/Footer.tsx — Site footer

import { TrendingUp, ExternalLink, Users } from 'lucide-react';

export default function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--color-border)',
      background: 'rgba(5,13,26,0.8)',
      backdropFilter: 'blur(12px)',
      marginTop: 'auto',
    }}>
      <div className="container" style={{ padding: '2.5rem 1.5rem', display:'flex', flexWrap:'wrap', gap:'2rem', justifyContent:'space-between', alignItems:'center' }}>
        {/* Brand */}
        <div style={{ display:'flex', alignItems:'center', gap:'0.6rem' }}>
          <div style={{ background:'linear-gradient(135deg,#3b82f6,#06b6d4)', borderRadius:'8px', padding:'6px', display:'flex' }}>
            <TrendingUp size={18} color="#fff" />
          </div>
          <div>
            <div style={{ fontFamily:'var(--font-heading)', fontWeight:800, color:'#fff' }}>
              Retail<span style={{ color:'#60a5fa' }}>IQ</span>
            </div>
            <div style={{ fontSize:'0.72rem', color:'var(--color-text-muted)' }}>v1.0.0 · AI Demand Forecasting</div>
          </div>
        </div>

        {/* Links */}
        <div style={{ display:'flex', gap:'1.5rem', flexWrap:'wrap' }}>
          {['Home','Forecast','Dashboard','History','Model Performance','About'].map(l => (
            <a key={l} href={`/${l.toLowerCase().replace(' ','-')}`}
               style={{ fontSize:'0.83rem', color:'var(--color-text-muted)', transition:'color 0.2s' }}
               onMouseOver={e => (e.currentTarget.style.color='#fff')}
               onMouseOut={e => (e.currentTarget.style.color='var(--color-text-muted)')}
            >{l}</a>
          ))}
        </div>

        {/* Social + copyright */}
        <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:'0.5rem' }}>
          <div style={{ display:'flex', gap:'1rem' }}>
            <a href="https://github.com" target="_blank" rel="noreferrer"
               style={{ color:'var(--color-text-muted)', transition:'color 0.2s' }}
               onMouseOver={e => (e.currentTarget.style.color='#fff')}
               onMouseOut={e => (e.currentTarget.style.color='var(--color-text-muted)')}
            ><ExternalLink size={18} /></a>
            <a href="https://linkedin.com" target="_blank" rel="noreferrer"
               style={{ color:'var(--color-text-muted)', transition:'color 0.2s' }}
               onMouseOver={e => (e.currentTarget.style.color='#0a66c2')}
               onMouseOut={e => (e.currentTarget.style.color='var(--color-text-muted)')}
            ><Users size={18} /></a>
          </div>
          <div style={{ fontSize:'0.75rem', color:'var(--color-text-faint)' }}>
            © {new Date().getFullYear()} RetailIQ · Multi-Series Forecasting Platform
          </div>
        </div>
      </div>
    </footer>
  );
}
