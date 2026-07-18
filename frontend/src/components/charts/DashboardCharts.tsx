// components/charts/DashboardCharts.tsx — All dashboard visualisation components

import Plot from 'react-plotly.js';

interface StoreCount { store: number; name: string; forecasts: number; }
interface ItemCount  { item: number;  name: string; forecasts: number; }

/* ---- Store Forecast Bar Chart ---- */
export function StoreForecastBar({ data }: { data: StoreCount[] }) {
  return (
    <Plot
      data={[{
        x: data.map(d => d.name.split(' ')[0]),
        y: data.map(d => d.forecasts),
        type: 'bar',
        marker: { color: data.map((_, i) => `hsl(${210 + i * 12},70%,${50 + i % 3 * 5}%)`) },
        text: data.map(d => String(d.forecasts)),
        textposition: 'auto',
      }]}
      layout={_darkLayout('Forecasts Generated per Store', 'Store', 'Forecasts')}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: '280px' }}
    />
  );
}

/* ---- Top Items Bar Chart ---- */
export function TopItemsBar({ data }: { data: ItemCount[] }) {
  const top = data.slice(0, 10);
  return (
    <Plot
      data={[{
        x: top.map(d => d.forecasts),
        y: top.map(d => d.name.length > 16 ? d.name.slice(0, 16) + '…' : d.name),
        type: 'bar',
        orientation: 'h',
        marker: { color: top.map((_, i) => `hsl(${270 - i * 12},65%,${55 + i % 3 * 5}%)`) },
      }]}
      layout={_darkLayout('Top Forecasted Items', 'Forecasts', 'Item')}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: '300px' }}
    />
  );
}

/* ---- Model Usage Pie ---- */
export function ModelUsagePie({ models }: { models: string[] }) {
  const counts: Record<string, number> = {};
  models.forEach(m => { counts[m] = (counts[m] || 0) + 1; });
  const labels = Object.keys(counts);
  const values = Object.values(counts);

  return (
    <Plot
      data={[{
        labels,
        values,
        type: 'pie',
        hole: 0.5,
        marker: { colors: ['#3b82f6','#8b5cf6','#06b6d4','#10b981','#f59e0b'] },
        textfont: { color: '#fff' },
      }]}
      layout={{
        ..._darkLayout('Model Usage Distribution'),
        showlegend: true,
        legend: { font: { color: '#94a3b8' }, bgcolor: 'rgba(0,0,0,0)' },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%', height: '260px' }}
    />
  );
}

/* ---- Shared dark layout factory ---- */
function _darkLayout(title: string, xLabel = '', yLabel = ''): Record<string, unknown> {
  return {
    title: { text: title, font: { color: '#e2e8f0', size: 13, family: 'Inter, sans-serif' } },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 11 },
    xaxis: { title: xLabel, gridcolor: 'rgba(96,165,250,0.07)', linecolor: 'rgba(96,165,250,0.12)', tickfont: { color: '#94a3b8' } },
    yaxis: { title: yLabel, gridcolor: 'rgba(96,165,250,0.07)', linecolor: 'rgba(96,165,250,0.12)', tickfont: { color: '#94a3b8' } },
    margin: { t: 40, r: 10, b: 50, l: 60 },
  };
}
