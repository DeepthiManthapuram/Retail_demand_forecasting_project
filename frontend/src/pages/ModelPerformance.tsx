// pages/ModelPerformance.tsx — Model comparison and saved model browser with PDF link

import { useEffect, useState } from 'react';
import { BarChart3, Cpu, RefreshCw, FileText } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { getModelInfo, predict, pdfUrl } from '../api/client';
import Plot from 'react-plotly.js';
import Footer from '../components/Footer';

interface SavedModel {
  model_name: string;
  store: number;
  item: number;
  path: string;
  modified_at: number;
}

const STORE_NAMES: Record<number, string> = {
  1:'Hyderabad Central', 2:'Mumbai Metro',    3:'Delhi North',    4:'Bangalore South',
  5:'Chennai East',      6:'Kolkata West',     7:'Pune City',      8:'Ahmedabad Hub',
  9:'Jaipur Royal',      10:'Surat Diamond',
};

const ITEM_NAMES: Record<number, string> = {
  1:'Whole Milk',      2:'Butter',         3:'Cheddar Cheese',  4:'Yogurt',         5:'Cream',
  6:'Orange Juice',    7:'Apple Juice',    8:'Mango Juice',     9:'Cola 2L',        10:'Green Tea',
  11:'Potato Chips',   12:'Popcorn',       13:'Biscuits',       14:'Cookies',       15:'Crackers',
  16:'Rice 5kg',       17:'Wheat Flour',   18:'Sugar 1kg',      19:'Salt 500g',     20:'Cooking Oil',
  21:'Frozen Pizza',   22:'Frozen Peas',   23:'Ice Cream',      24:'Frozen Chicken',25:'Frozen Fish',
  26:'Shampoo 200ml',  27:'Conditioner',   28:'Soap Bar',       29:'Toothpaste',    30:'Body Lotion',
  31:'Dishwash Liquid',32:'Laundry Powder',33:'Floor Cleaner',  34:'Toilet Paper',  35:'Paper Towels',
  36:'White Bread',    37:'Brown Bread',   38:'Croissant',      39:'Bagel',         40:'Sourdough',
  41:'Banana 1kg',     42:'Apple 1kg',     43:'Tomato 500g',    44:'Spinach',       45:'Carrot 500g',
  46:'Chicken Breast', 47:'Beef Mince',    48:'Pork Ribs',      49:'Lamb Chops',    50:'Tuna Can',
};

const MODEL_COLORS: Record<string, string> = {
  xgboost:'#3b82f6', lightgbm:'#8b5cf6', random_forest:'#06b6d4',
  lstm:'#10b981', gru:'#f59e0b', arima:'#ef4444', sarima:'#ec4899',
  prophet:'#f97316', naive:'#94a3b8', moving_average:'#a78bfa',
};

const ALL_MODEL_TYPES = [
  'xgboost', 'lightgbm', 'random_forest', 'lstm', 'gru',
  'arima', 'prophet', 'naive', 'moving_average'
];

export default function ModelPerformance() {
  const [models, setModels]     = useState<SavedModel[]>([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [selected, setSelected] = useState<string>('all');
  const [pdfGenerating, setPdfGenerating] = useState<Record<string, boolean>>({});

  const load = async () => {
    setLoading(true); setError('');
    try {
      const info = await getModelInfo();
      setModels(info.saved_models || []);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const displayed = selected === 'all' ? models : models.filter(m => m.model_name.toLowerCase() === selected.toLowerCase());

  // Count by model type (pre-populate ALL models with 0 so they show up in chart/filters)
  const typeCount: Record<string, number> = {};
  ALL_MODEL_TYPES.forEach(t => { typeCount[t] = 0; });
  models.forEach(m => {
    const name = m.model_name.toLowerCase();
    typeCount[name] = (typeCount[name] || 0) + 1;
  });

  return (
    <div style={{ paddingTop:'80px', minHeight:'100vh' }}>
      <div className="container section">
        <div className="page-header" style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'1rem' }}>
          <div>
            <h1><BarChart3 size={26} style={{ verticalAlign:'middle', marginRight:10, color:'#60a5fa' }} />Model Performance</h1>
            <p>Explore saved model artefacts, training statistics, and download PDF reports.</p>
          </div>
          <button className="btn btn-outline" onClick={load}><RefreshCw size={14} /> Refresh</button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom:'1rem' }}>{error}</div>}
        {loading && <LoadingSpinner label="Loading models…" />}

        {!loading && (
          <>
            {/* ── Summary KPIs ── */}
            <div className="grid-4" style={{ marginBottom:'2rem' }}>
              <div className="kpi-card">
                <div className="kpi-value" style={{ color:'#3b82f6' }}>{models.length}</div>
                <div className="kpi-label">Saved Models</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-value" style={{ color:'#8b5cf6' }}>{ALL_MODEL_TYPES.length}</div>
                <div className="kpi-label">Supported Model Types</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-value" style={{ color:'#06b6d4' }}>{new Set(models.map(m=>m.store)).size}</div>
                <div className="kpi-label">Trained Stores</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-value" style={{ color:'#10b981' }}>{new Set(models.map(m=>m.item)).size}</div>
                <div className="kpi-label">Trained Products</div>
              </div>
            </div>

            {/* ── Model Count Chart ── */}
            <div className="glass-card" style={{ padding:'1.5rem', marginBottom:'2rem' }}>
              <h3 style={{ fontSize:'0.95rem', marginBottom:'0.5rem', color:'var(--color-text-muted)' }}>Models on Disk by Type</h3>
              <Plot
                data={[{
                  x: Object.keys(typeCount).map(k => k.toUpperCase()),
                  y: Object.values(typeCount),
                  type: 'bar',
                  marker: { color: Object.keys(typeCount).map(k => MODEL_COLORS[k] || '#60a5fa') },
                }]}
                layout={{
                  paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
                  font:{ family:'Inter, sans-serif', color:'#94a3b8', size:12 },
                  xaxis:{ gridcolor:'rgba(96,165,250,0.07)', linecolor:'rgba(96,165,250,0.12)' },
                  yaxis:{ gridcolor:'rgba(96,165,250,0.07)', linecolor:'rgba(96,165,250,0.12)', title:'Count', dtick: 1 },
                  margin:{ t:20, r:10, b:40, l:50 },
                }}
                config={{ displayModeBar:false, responsive:true }}
                style={{ width:'100%', height:'200px' }}
              />
            </div>

            {/* ── Filter ── */}
            <div style={{ display:'flex', gap:'0.5rem', marginBottom:'1.5rem', flexWrap:'wrap' }}>
              {['all', ...ALL_MODEL_TYPES].map(t => (
                <button key={t}
                  className={`btn ${selected === t ? 'btn-primary' : 'btn-outline'}`}
                  style={{ padding:'0.35rem 1rem', fontSize:'0.82rem' }}
                  onClick={() => setSelected(t)}>
                  {t === 'all' ? 'All Models' : t.toUpperCase()}
                </button>
              ))}
            </div>

            {/* ── Model Table ── */}
            <div className="glass-card" style={{ padding:'1.5rem' }}>
              <h3 style={{ fontSize:'1rem', marginBottom:'1rem', color:'var(--color-text-muted)' }}>Saved Model Files</h3>
              <div style={{ overflowX:'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>S.No</th>
                      <th>Model Type</th>
                      <th>Store Name</th>
                      <th>Product Name</th>
                      <th>Saved At</th>
                      <th>File Name</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayed.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ textAlign:'center', padding:'2rem', color:'var(--color-text-faint)' }}>
                          No saved models found for the selected type.
                        </td>
                      </tr>
                    ) : (
                      displayed.map((m, i) => {
                        const key = `${m.store}-${m.item}-${m.model_name}-${i}`;
                        const isGen = pdfGenerating[key];
                        return (
                          <tr key={i}>
                            <td style={{ color:'var(--color-text-faint)' }}>{i+1}</td>
                            <td>
                              <span className="badge" style={{ background:`rgba(${hexToRgb(MODEL_COLORS[m.model_name.toLowerCase()]||'#60a5fa')},0.15)`, color: MODEL_COLORS[m.model_name.toLowerCase()]||'#60a5fa' }}>
                                <Cpu size={11} /> {m.model_name.toUpperCase()}
                              </span>
                            </td>
                            <td>{STORE_NAMES[m.store] || `Store ${m.store}`}</td>
                            <td>{ITEM_NAMES[m.item] || `Item ${m.item}`}</td>
                            <td style={{ fontSize:'0.8rem', color:'var(--color-text-muted)' }}>
                              {new Date(m.modified_at * 1000).toLocaleString()}
                            </td>
                            <td style={{ fontSize:'0.75rem', color:'var(--color-text-faint)', maxWidth:180, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                              {m.path.split(/[\\/]/).pop()}
                            </td>
                            <td>
                              <div style={{ display:'flex', gap:'0.4rem' }}>
                                <button
                                  className="btn btn-ghost"
                                  style={{ padding:'0.25rem 0.6rem', fontSize:'0.75rem', display:'inline-flex', alignItems:'center', gap:4 }}
                                  onClick={async () => {
                                    setPdfGenerating(prev => ({ ...prev, [key]: true }));
                                    try {
                                      const res = await predict({
                                        store: m.store,
                                        item: m.item,
                                        horizon: 30,
                                        model: m.model_name.toLowerCase()
                                      });
                                      if (res && (res as any).forecast_id) {
                                        window.open(pdfUrl((res as any).forecast_id), '_blank');
                                      } else {
                                        alert('Forecast generated! Find it in the Forecast History page.');
                                      }
                                    } catch (e) {
                                      console.error(e);
                                      alert('Failed to generate PDF. Make sure backend is running.');
                                    } finally {
                                      setPdfGenerating(prev => ({ ...prev, [key]: false }));
                                    }
                                  }}
                                  disabled={isGen}
                                >
                                  <FileText size={12} /> {isGen ? 'Opening...' : 'Open PDF'}
                                </button>
                                <button
                                  className="btn btn-outline"
                                  style={{ padding:'0.25rem 0.6rem', fontSize:'0.75rem', display:'inline-flex', alignItems:'center', gap:4 }}
                                  onClick={async () => {
                                    setPdfGenerating(prev => ({ ...prev, [key]: true }));
                                    try {
                                      const res = await predict({
                                        store: m.store,
                                        item: m.item,
                                        horizon: 30,
                                        model: m.model_name.toLowerCase()
                                      });
                                      if (res && (res as any).forecast_id) {
                                        // We force download by using standard dynamic download method
                                        const url = pdfUrl((res as any).forecast_id);
                                        const link = document.createElement('a');
                                        link.href = url;
                                        link.target = '_blank';
                                        link.download = `Forecast_Report_${m.model_name}_Store${m.store}_Item${m.item}.pdf`;
                                        document.body.appendChild(link);
                                        link.click();
                                        document.body.removeChild(link);
                                      } else {
                                        alert('Forecast generated! Find it in the Forecast History page.');
                                      }
                                    } catch (e) {
                                      console.error(e);
                                      alert('Failed to download PDF.');
                                    } finally {
                                      setPdfGenerating(prev => ({ ...prev, [key]: false }));
                                    }
                                  }}
                                  disabled={isGen}
                                >
                                  <FileText size={12} /> {isGen ? 'Downloading...' : 'Download PDF'}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
      <Footer />
    </div>
  );
}

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `${r},${g},${b}`;
}
