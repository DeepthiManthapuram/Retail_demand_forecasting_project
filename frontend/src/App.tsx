import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar           from './components/Navbar';
import Home             from './pages/Home';
import Forecast         from './pages/Forecast';
import Dashboard        from './pages/Dashboard';
import HistoryPage      from './pages/History';

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display:'flex', flexDirection:'column', minHeight:'100vh' }}>
        <Navbar />
        <main style={{ flex: 1 }}>
          <Routes>
            <Route path="/"                 element={<Home />} />
            <Route path="/forecast"         element={<Forecast />} />
            <Route path="/dashboard"        element={<Dashboard />} />
            <Route path="/history"          element={<HistoryPage />} />
            <Route path="*" element={
              <div style={{ textAlign:'center', padding:'8rem 1rem', color:'var(--color-text-muted)' }}>
                <h2 style={{ fontSize:'3rem', marginBottom:'0.5rem' }}>404</h2>
                <p>Page not found.</p>
                <a href="/" className="btn btn-primary" style={{ marginTop:'1.5rem', display:'inline-flex' }}>Go Home</a>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
