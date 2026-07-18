// pages/About.tsx — Project information, models, and architecture

import { Brain, Database, BarChart2, Shield, Zap } from 'lucide-react';
import Footer from '../components/Footer';

const MODELS = [
  { name:'Naïve / Moving Average', type:'Baseline',  desc:'Simple benchmarks — last value and rolling mean.' },
  { name:'ARIMA / SARIMA',          type:'Statistical',desc:'Auto-regressive integrated models for trend & seasonality.' },
  { name:'Prophet',                 type:'Statistical',desc:'Facebook/Meta Prophet with Indian holiday calendars.' },
  { name:'Random Forest',           type:'ML',        desc:'Ensemble of 300 decision trees with bootstrap intervals.' },
  { name:'XGBoost',                 type:'ML',        desc:'Gradient boosting with early stopping; top-ranked on Kaggle.' },
  { name:'LightGBM',                type:'ML',        desc:'Fast gradient boosting; ideal for large datasets.' },
  { name:'LSTM',                    type:'Deep Learning',desc:'Long Short-Term Memory recurrent network (64+32 units).' },
  { name:'GRU',                     type:'Deep Learning',desc:'Gated Recurrent Unit — faster than LSTM, similar accuracy.' },
];

const TYPE_COLORS: Record<string,string> = {
  Baseline:'#94a3b8', Statistical:'#06b6d4', ML:'#3b82f6', 'Deep Learning':'#8b5cf6',
};

const ARCH_SECTIONS = [
  { icon: Database,  title:'Data Layer',       desc:'SQLite → PostgreSQL. SQLAlchemy ORM with 7 normalised tables: stores, products, sales, forecasts, users, prediction_logs, model_metrics.' },
  { icon: BarChart2, title:'Feature Engineering',desc:'Time features (cyclic sin/cos), lag features (1,7,14,30 days), rolling statistics (mean, std, min, max, median, EWM), target encoding, one-hot encoding.' },
  { icon: Brain,     title:'Model Layer',       desc:'9 model families. BaseForecaster abstract class enforces fit(), predict(), predict_interval(), save(), load() interface across all models.' },
  { icon: Zap,       title:'Prediction Engine', desc:'DemandPredictor with LRU model cache, future feature builder, post-processor (clip→round→int), and confidence interval generator.' },
  { icon: Shield,    title:'API Layer',         desc:'FastAPI with JWT authentication, background training tasks, CSV/Excel/PDF report downloads, and OpenAPI documentation.' },
];

export default function About() {
  return (
    <div style={{ paddingTop:'80px', minHeight:'100vh' }}>
      <div className="container section">

        {/* Header */}
        <div className="page-header" style={{ textAlign:'center', marginBottom:'3rem' }}>
          <h1>Multi-Series Forecasting for<br />
            <span className="text-gradient">Retail Demand Optimization</span>
          </h1>
          <p style={{ maxWidth:640, margin:'0.75rem auto 0', fontSize:'1.05rem', lineHeight:1.7 }}>
            A production-grade end-to-end machine learning application predicting daily demand
            across 500 Store × Item time series using 9 ML/DL models.
          </p>
        </div>

        {/* Project goal */}
        <div className="glass-card" style={{ padding:'2rem', marginBottom:'2rem' }}>
          <h2 style={{ fontSize:'1.3rem', marginBottom:'1rem' }}>Project Objective</h2>
          <p style={{ color:'var(--color-text-muted)', lineHeight:1.8 }}>
            Retailers face two costly problems: <strong style={{ color:'#ef4444' }}>stock shortages</strong> that drive customers away,
            and <strong style={{ color:'#f59e0b' }}>overstock</strong> that ties up working capital. This platform uses historical daily
            sales data (date, store, item, sales) combined with derived features — seasonality, holidays, promotions,
            weather, lag statistics — to forecast future demand with quantified uncertainty.
          </p>
          <div style={{ display:'flex', gap:'1rem', flexWrap:'wrap', marginTop:'1.25rem' }}>
            {['Reduce stock shortages','Eliminate overstock','Optimise warehouse planning',
              'Improve supply chain','Increase inventory turn','Data-driven decisions'].map(b => (
              <span key={b} className="badge badge-blue" style={{ padding:'0.3rem 0.8rem', fontSize:'0.8rem' }}>✓ {b}</span>
            ))}
          </div>
        </div>

        {/* Models grid */}
        <h2 style={{ fontSize:'1.3rem', marginBottom:'1.25rem' }}>Implemented Models</h2>
        <div className="grid-4" style={{ marginBottom:'2.5rem' }}>
          {MODELS.map(m => (
            <div key={m.name} className="glass-card" style={{ padding:'1.25rem' }}>
              <span className="badge" style={{
                background:`rgba(${hexToRgb(TYPE_COLORS[m.type])},0.12)`,
                color: TYPE_COLORS[m.type], fontSize:'0.7rem', marginBottom:'0.75rem', display:'inline-flex',
              }}>{m.type}</span>
              <h4 style={{ fontSize:'0.92rem', marginBottom:'0.4rem' }}>{m.name}</h4>
              <p style={{ color:'var(--color-text-muted)', fontSize:'0.8rem', lineHeight:1.5 }}>{m.desc}</p>
            </div>
          ))}
        </div>

        {/* Architecture */}
        <h2 style={{ fontSize:'1.3rem', marginBottom:'1.25rem' }}>System Architecture</h2>
        <div className="grid-3" style={{ marginBottom:'2.5rem' }}>
          {ARCH_SECTIONS.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="glass-card" style={{ padding:'1.5rem' }}>
              <div style={{ display:'flex', alignItems:'center', gap:'0.75rem', marginBottom:'0.75rem' }}>
                <Icon size={20} color="#60a5fa" />
                <h4 style={{ fontSize:'0.95rem' }}>{title}</h4>
              </div>
              <p style={{ color:'var(--color-text-muted)', fontSize:'0.83rem', lineHeight:1.6 }}>{desc}</p>
            </div>
          ))}
        </div>

        {/* Tech stack table */}
        <div className="glass-card" style={{ padding:'2rem', marginBottom:'2rem' }}>
          <h2 style={{ fontSize:'1.3rem', marginBottom:'1.25rem' }}>Technology Stack</h2>
          <div style={{ overflowX:'auto' }}>
            <table className="data-table">
              <thead><tr><th>Layer</th><th>Technology</th><th>Purpose</th></tr></thead>
              <tbody>
                {[
                  ['Language',     'Python 3.12+',              'Core ML/API backend'],
                  ['API',          'FastAPI',                    'High-performance REST API'],
                  ['ML Models',    'Scikit-learn, XGBoost, LightGBM','Gradient boosting & ensembles'],
                  ['Deep Learning','TensorFlow / Keras',         'LSTM & GRU neural networks'],
                  ['Time Series',  'Prophet, Statsmodels',       'ARIMA, SARIMA, Prophet'],
                  ['Features',     'Pandas, NumPy',             'Feature engineering pipeline'],
                  ['Database',     'SQLAlchemy + SQLite/PostgreSQL','ORM and persistence'],
                  ['Auth',         'python-jose, passlib',       'JWT + bcrypt authentication'],
                  ['Frontend',     'React 18 + TypeScript',      'SPA user interface'],
                  ['Charts',       'Plotly.js + react-plotly.js','Interactive visualisations'],
                  ['State',        'Zustand',                    'Lightweight global state'],
                  ['Dev Server',   'Vite',                       'Fast build & HMR'],
                  ['Containerisation','Docker + Docker Compose',  'Reproducible deployment'],
                ].map(([layer, tech, purpose]) => (
                  <tr key={layer}>
                    <td style={{ fontWeight:600, color:'var(--color-primary-h)' }}>{layer}</td>
                    <td style={{ color:'var(--color-text)' }}>{tech}</td>
                    <td style={{ color:'var(--color-text-muted)', fontSize:'0.87rem' }}>{purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `${r},${g},${b}`;
}
