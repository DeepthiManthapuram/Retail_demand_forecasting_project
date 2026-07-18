// pages/History.tsx — Forecast history with filters and download links (PDF only)

import { useEffect, useState } from 'react';
import { History as HistoryIcon, FileText, Filter } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { getForecastHistory, pdfUrl } from '../api/client';
import type { ForecastHistoryItem } from '../types';

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

export default function HistoryPage() {
  const [data, setData]         = useState<ForecastHistoryItem[]>([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [storeFilter, setStore] = useState('');
  const [itemFilter, setItem]   = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await getForecastHistory(
        storeFilter ? +storeFilter : undefined,
        itemFilter  ? +itemFilter  : undefined,
        100,
      );
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div style={{ paddingTop:'80px', minHeight:'100vh' }}>
      <div className="container section">
        <div className="page-header">
          <h1><HistoryIcon size={26} style={{ verticalAlign:'middle', marginRight:10, color:'#60a5fa' }} />Forecast History</h1>
          <p>Browse, review, and download all past forecast records as PDF reports.</p>
        </div>

        {/* Filters */}
        <div className="glass-card" style={{ padding:'1.5rem', marginBottom:'1.5rem' }}>
          <div style={{ display:'flex', gap:'1.25rem', flexWrap:'wrap', alignItems:'flex-end' }}>
            <div style={{ minWidth:220, flex: 1 }}>
              <label className="label"><Filter size={12} /> Store</label>
              <select className="select" value={storeFilter} onChange={e => setStore(e.target.value)}>
                <option value="">All Stores</option>
                {Object.entries(STORE_NAMES).map(([id, name]) => (
                  <option key={id} value={id}>{name}</option>
                ))}
              </select>
            </div>
            <div style={{ minWidth:220, flex: 1 }}>
              <label className="label"><Filter size={12} /> Product</label>
              <select className="select" value={itemFilter} onChange={e => setItem(e.target.value)}>
                <option value="">All Products</option>
                {Object.entries(ITEM_NAMES).map(([id, name]) => (
                  <option key={id} value={id}>{name}</option>
                ))}
              </select>
            </div>
            <button className="btn btn-primary" onClick={load} style={{ minWidth:120 }}>Apply Filters</button>
          </div>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom:'1rem' }}>{error}</div>}
        {loading && <LoadingSpinner label="Loading history…" />}

        {!loading && (
          <div className="glass-card" style={{ padding:'1.5rem' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1rem' }}>
              <h3 style={{ fontSize:'0.95rem', color:'var(--color-text-muted)' }}>{data.length} Records Found</h3>
            </div>

            {data.length === 0
              ? <div style={{ textAlign:'center', padding:'3rem', color:'var(--color-text-faint)' }}>
                  No forecast history found matching these filters. Run a prediction first!
                </div>
              : (
                <div style={{ overflowX:'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th><th>Store Name</th><th>Product Name</th>
                        <th>Horizon</th><th>Avg Forecast</th><th>Created At</th><th>PDF Report</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map(row => (
                        <tr key={row.id}>
                          <td style={{ color:'var(--color-text-faint)' }}>#{row.id}</td>
                          <td>{row.store_name}</td>
                          <td>{row.item_name}</td>
                          <td>{row.horizon} Days</td>
                          <td style={{ color:'#10b981', fontWeight:600 }}>{row.avg_forecast.toFixed(0)} units</td>
                          <td style={{ fontSize:'0.8rem', color:'var(--color-text-muted)' }}>
                            {new Date(row.created_at).toLocaleString()}
                          </td>
                          <td>
                            <a href={`${pdfUrl(row.id)}?current_stock=120`} target="_blank" rel="noreferrer" className="btn btn-ghost" style={{ padding:'0.25rem 0.6rem', fontSize:'0.75rem', display:'inline-flex', alignItems:'center', gap:4 }}>
                              <FileText size={12} /> PDF Summary
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
          </div>
        )}
      </div>
    </div>
  );
}
