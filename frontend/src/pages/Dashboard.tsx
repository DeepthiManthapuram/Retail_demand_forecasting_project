// pages/Dashboard.tsx — Live KPI dashboard with charts and mapped store/item names

import { useEffect } from 'react';
import { Activity, Store, Package, TrendingUp, Zap } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { StoreForecastBar, TopItemsBar } from '../components/charts/DashboardCharts';
import { getDashboard } from '../api/client';
import { useAppStore } from '../store/useAppStore';

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

export default function Dashboard() {
  const { dashboardData, dashboardLoading, setDashboardData, setDashboardLoading } = useAppStore();

  useEffect(() => {
    setDashboardLoading(true);
    getDashboard()
      .then(setDashboardData)
      .catch(console.error)
      .finally(() => setDashboardLoading(false));
  }, []);

  if (dashboardLoading) return <div style={{ paddingTop:100 }}><LoadingSpinner label="Loading dashboard…" /></div>;

  const kpi = dashboardData?.kpi;
  const recent = dashboardData?.recent_predictions ?? [];
  const storeCounts = dashboardData?.store_forecast_counts ?? [];
  const itemCounts  = dashboardData?.item_forecast_counts  ?? [];

  const kpiCards = [
    { label:'Total Stores',       value: kpi?.total_stores  ?? 10,   icon: Store,     color:'#3b82f6' },
    { label:'Total Items',        value: kpi?.total_items   ?? 50,   icon: Package,   color:'#8b5cf6' },
    { label:'Time Series',        value: kpi?.total_series  ?? 500,  icon: TrendingUp,color:'#06b6d4' },
    { label:'Forecasts Today',    value: kpi?.forecasts_today ?? 0,  icon: Zap,       color:'#10b981' },
    { label:'Total Predictions',  value: kpi?.total_predictions ?? 0,icon: Activity,  color:'#f59e0b' },
  ];

  return (
    <div style={{ paddingTop:'80px', minHeight:'100vh' }}>
      <div className="container section">
        <div className="page-header">
          <h1><Activity size={26} style={{ verticalAlign:'middle', marginRight:10, color:'#60a5fa' }} />Dashboard</h1>
          <p>Real-time overview of the forecasting platform metrics and activity.</p>
        </div>

        {/* ── KPI Cards ── */}
        <div className="grid-4" style={{ marginBottom:'2.5rem' }}>
          {kpiCards.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="kpi-card">
              <div style={{ display:'flex', justifyContent:'center', marginBottom:'0.75rem' }}>
                <div style={{ width:40, height:40, borderRadius:10, background:`rgba(${hexToRgb(color)},0.12)`,
                  border:`1px solid rgba(${hexToRgb(color)},0.25)`, display:'flex', alignItems:'center', justifyContent:'center' }}>
                  <Icon size={18} color={color} />
                </div>
              </div>
              <div className="kpi-value" style={{ color, fontSize: typeof value === 'string' ? '1.1rem' : '2rem' }}>{value}</div>
              <div className="kpi-label">{label}</div>
            </div>
          ))}
        </div>

        {/* ── Charts Row ── */}
        <div className="grid-2" style={{ marginBottom:'2rem' }}>
          <div className="glass-card" style={{ padding:'1.5rem' }}>
            <h3 style={{ fontSize:'0.95rem', marginBottom:'0.5rem', color:'var(--color-text-muted)' }}>Store Forecast Activity</h3>
            {storeCounts.length > 0 ? <StoreForecastBar data={storeCounts} /> :
              <div style={{ textAlign:'center', padding:'2rem', color:'var(--color-text-faint)' }}>No data yet</div>}
          </div>
          <div className="glass-card" style={{ padding:'1.5rem' }}>
            <h3 style={{ fontSize:'0.95rem', marginBottom:'0.5rem', color:'var(--color-text-muted)' }}>Top Forecasted Items</h3>
            {itemCounts.length > 0 ? <TopItemsBar data={itemCounts} /> :
              <div style={{ textAlign:'center', padding:'2rem', color:'var(--color-text-faint)' }}>No data yet</div>}
          </div>
        </div>

        {/* ── Recent Activity ── */}
        <div className="glass-card" style={{ padding:'1.5rem', marginBottom:'2rem' }}>
          <h3 style={{ fontSize:'0.95rem', marginBottom:'1rem', color:'var(--color-text-muted)' }}>Recent Prediction Requests</h3>
          {recent.length === 0
            ? <div style={{ textAlign:'center', padding:'2rem', color:'var(--color-text-faint)' }}>No predictions yet — try the Forecast page!</div>
            : (
              <div style={{ overflowX:'auto' }}>
                <table className="data-table">
                  <thead><tr><th>Store Name</th><th>Product Name</th><th>Horizon</th><th>Status</th></tr></thead>
                  <tbody>
                    {recent.map((r, i) => (
                      <tr key={i}>
                        <td>{STORE_NAMES[r.store] || `Store ${r.store}`}</td>
                        <td>{ITEM_NAMES[r.item] || `Item ${r.item}`}</td>
                        <td>{r.horizon}d</td>
                        <td><span className={`badge ${r.status === 'success' ? 'badge-green' : 'badge-yellow'}`}>{r.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `${r},${g},${b}`;
}
