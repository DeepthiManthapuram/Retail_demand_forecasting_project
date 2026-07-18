// components/charts/ForecastChart.tsx — Interactive forecast visualisation

import Plot from 'react-plotly.js';
import type { PredictResponse } from '../../types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type PlotData = any;
type PlotLayout = any;

interface Props {
  data: PredictResponse;
  historicalDates?: string[];
  historicalSales?: number[];
}

export default function ForecastChart({ data, historicalDates = [], historicalSales = [] }: Props) {
  const traces: PlotData[] = [];

  // Historical sales line
  if (historicalDates.length > 0) {
    traces.push({
      x: historicalDates,
      y: historicalSales,
      type: 'scatter',
      mode: 'lines',
      name: 'Historical Sales',
      line: { color: '#60a5fa', width: 2 },
    });
  }

  // Confidence interval band
  if (data.upper_bound.length > 0) {
    traces.push({
      x: [...data.forecast_dates, ...[...data.forecast_dates].reverse()],
      y: [...data.upper_bound, ...[...data.lower_bound].reverse()],
      fill: 'toself',
      fillcolor: 'rgba(139,92,246,0.12)',
      line: { color: 'transparent' },
      name: '90% Confidence Interval',
      type: 'scatter',
      hoverinfo: 'skip',
    });
  }

  // Forecast line
  traces.push({
    x: data.forecast_dates,
    y: data.predicted_sales,
    type: 'scatter',
    mode: 'lines+markers',
    name: `Forecast (${data.model_used})`,
    line: { color: '#8b5cf6', width: 2.5, dash: 'dot' },
    marker: { size: 5, color: '#8b5cf6' },
  });

  // Upper bound line
  if (data.upper_bound.length > 0) {
    traces.push({
      x: data.forecast_dates,
      y: data.upper_bound,
      type: 'scatter',
      mode: 'lines',
      name: 'Upper Bound',
      line: { color: '#06b6d4', width: 1, dash: 'dash' },
    });

    traces.push({
      x: data.forecast_dates,
      y: data.lower_bound,
      type: 'scatter',
      mode: 'lines',
      name: 'Lower Bound',
      line: { color: '#06b6d4', width: 1, dash: 'dash' },
    });
  }

  const layout: PlotLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 12 },
    xaxis: {
      title: 'Date',
      gridcolor: 'rgba(96,165,250,0.08)',
      linecolor: 'rgba(96,165,250,0.15)',
      tickfont: { color: '#94a3b8' },
    },
    yaxis: {
      title: 'Daily Sales (units)',
      gridcolor: 'rgba(96,165,250,0.08)',
      linecolor: 'rgba(96,165,250,0.15)',
      tickfont: { color: '#94a3b8' },
    },
    legend: {
      bgcolor: 'rgba(5,13,26,0.6)',
      bordercolor: 'rgba(96,165,250,0.2)',
      borderwidth: 1,
      font: { color: '#94a3b8' },
    },
    hoverlabel: { bgcolor: 'rgba(10,22,40,0.9)', bordercolor: '#3b82f6', font: { color: '#fff' } },
    margin: { t: 10, r: 10, b: 60, l: 60 },
    hovermode: 'x unified',
  };

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ displayModeBar: true, responsive: true, displaylogo: false }}
      style={{ width: '100%', height: '420px' }}
    />
  );
}
