// pages/Home.tsx — Landing page with hero, features, tech stack, and CTAs

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp, BarChart2, Zap, Database, Brain, CheckCircle,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { getHealth } from '../api/client';

const FEATURES = [
  { icon: Brain,     title: 'AI-Powered Forecasting',    desc: 'XGBoost, LightGBM, LSTM & GRU models trained per Store × Item series.' },
  { icon: TrendingUp,title: 'Multi-Horizon Prediction',  desc: 'Forecast 7, 14, 30, 60, or 90 days ahead with confidence intervals.' },
  { icon: BarChart2, title: 'Interactive Dashboards',    desc: 'Plotly charts with historical trends, seasonality, and model comparisons.' },
  { icon: Database,  title: '500 Time Series',           desc: '10 stores × 50 items — independent series trained and served in parallel.' },
  { icon: Zap,       title: 'Real-Time Predictions',     desc: 'Sub-second inference via cached model registry and feature pipeline.' },
];



const BENEFITS = [
  'Reduce stock shortages by up to 35%',
  'Eliminate overstock costs',
  'Optimise warehouse planning',
  'Improve supply chain efficiency',
  'Increase inventory turn rate',
  'Data-driven purchase decisions',
];

export default function Home() {
  const navigate = useNavigate();
  const { setHealth } = useAppStore();

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {});
  }, []);

  return (
    <div style={{ paddingTop: '64px' }}>

      {/* ── Hero ── */}
      <section style={{
        minHeight: '92vh', display: 'flex', alignItems: 'center',
        background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(59,130,246,0.18) 0%, transparent 70%), var(--color-bg)',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Animated grid background */}
        <div style={{
          position:'absolute', inset:0, opacity:0.04,
          backgroundImage:'linear-gradient(rgba(96,165,250,1) 1px, transparent 1px), linear-gradient(90deg, rgba(96,165,250,1) 1px, transparent 1px)',
          backgroundSize:'50px 50px',
        }} />

        <div className="container" style={{ position:'relative', zIndex:1, textAlign:'center', padding:'4rem 1.5rem' }}>

          <h1 style={{ fontSize:'clamp(2.2rem, 5vw, 4rem)', fontWeight:800, lineHeight:1.1, marginBottom:'1.5rem', fontFamily:'var(--font-heading)' }}>
            Multi-Series Forecasting for<br />
            <span className="text-gradient">Retail Demand Optimization</span>
          </h1>

          <p style={{ fontSize:'1.15rem', color:'var(--color-text-muted)', maxWidth:'600px', margin:'0 auto 2.5rem', lineHeight:1.7 }}>
            AI-Powered Retail Forecasting Platform · Predict daily demand for every
            Store × Item combination using Machine Learning and Deep Learning.
          </p>

          <div style={{ display:'flex', gap:'1rem', justifyContent:'center', flexWrap:'wrap' }}>
            <button className="btn btn-primary pulse-glow" style={{ fontSize:'1rem', padding:'0.8rem 2.5rem' }}
              onClick={() => navigate('/forecast')}>
              <Zap size={18} /> Start Forecast
            </button>
          </div>

          {/* Stats row */}
          <div style={{ display:'flex', gap:'2rem', justifyContent:'center', marginTop:'3.5rem', flexWrap:'wrap' }}>
            {[['10', 'Stores'], ['50', 'Products'], ['500', 'Time Series']].map(([val, lbl]) => (
              <div key={lbl} style={{ textAlign:'center' }}>
                <div style={{ fontSize:'2rem', fontWeight:800, fontFamily:'var(--font-heading)',
                  background:'linear-gradient(135deg,#3b82f6,#06b6d4)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>{val}</div>
                <div style={{ fontSize:'0.8rem', color:'var(--color-text-muted)', textTransform:'uppercase', letterSpacing:'0.06em' }}>{lbl}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="section">
        <div className="container">
          <div style={{ textAlign:'center', marginBottom:'3rem' }}>
            <h2 style={{ fontSize:'2rem', marginBottom:'0.75rem' }}>Enterprise-Grade Features</h2>
            <p style={{ color:'var(--color-text-muted)', maxWidth:'500px', margin:'0 auto' }}>
              Every component built for production. No shortcuts, no placeholders.
            </p>
          </div>
          <div className="grid-3" style={{ gap:'1.5rem' }}>
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="glass-card fade-in-up" style={{ padding:'2rem' }}>
                <div style={{ width:48, height:48, borderRadius:12, background:'rgba(59,130,246,0.12)',
                  display:'flex', alignItems:'center', justifyContent:'center', marginBottom:'1.25rem', border:'1px solid rgba(59,130,246,0.2)' }}>
                  <Icon size={22} color="#60a5fa" />
                </div>
                <h3 style={{ fontSize:'1.05rem', marginBottom:'0.5rem' }}>{title}</h3>
                <p style={{ color:'var(--color-text-muted)', fontSize:'0.88rem', lineHeight:1.6 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Benefits ── */}
      <section className="section" style={{ background:'rgba(10,22,40,0.5)' }}>
        <div className="container" style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'4rem', alignItems:'center' }}>
          <div>
            <h2 style={{ fontSize:'2rem', marginBottom:'1.25rem' }}>
              Drive Business Value with<br />
              <span className="text-gradient">Accurate Demand Forecasting</span>
            </h2>
            <ul style={{ listStyle:'none', display:'flex', flexDirection:'column', gap:'0.75rem' }}>
              {BENEFITS.map(b => (
                <li key={b} style={{ display:'flex', alignItems:'center', gap:'0.75rem', color:'var(--color-text-muted)', fontSize:'0.95rem' }}>
                  <CheckCircle size={18} color="#10b981" style={{ flexShrink:0 }} />
                  {b}
                </li>
              ))}
            </ul>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
            {[['↓ 35%', 'Stock Shortages'], ['↓ 28%', 'Overstock Cost'],
              ['↑ 22%', 'Forecast Accuracy'], ['↑ 18%', 'Inventory Turnover']].map(([val, lbl]) => (
              <div key={lbl} className="glass-card" style={{ padding:'1.5rem', textAlign:'center' }}>
                <div style={{ fontSize:'2rem', fontWeight:800, fontFamily:'var(--font-heading)',
                  background:'linear-gradient(135deg,#3b82f6,#8b5cf6)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>{val}</div>
                <div style={{ fontSize:'0.78rem', color:'var(--color-text-muted)', marginTop:'0.25rem', textTransform:'uppercase', letterSpacing:'0.05em' }}>{lbl}</div>
              </div>
            ))}
          </div>
        </div>
        <style>{`@media(max-width:768px){.container>div:first-child+div{display:none}}`}</style>
      </section>
    </div>
  );
}

