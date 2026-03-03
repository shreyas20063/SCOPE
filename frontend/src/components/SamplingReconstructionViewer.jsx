/**
 * SamplingReconstructionViewer — Redesigned
 *
 * Layout:
 *   1. NyquistGauge   — SVG frequency bar showing fmax vs fs/2
 *   2. Info Cards      — fs, fmax, fs/2, Nyquist ratio
 *   3. Dual plots      — Time domain (left) + Frequency spectrum (right)
 *   4. Reconstruction  — Full-width, shown when methods toggled on
 *   5. Error plot      — Full-width, optional
 */

import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import './SamplingReconstructionViewer.css';

/* -----------------------------------------------------------------------
   Theme hook
   ----------------------------------------------------------------------- */
function useTheme() {
  const [theme, setTheme] = React.useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );

  React.useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
    return () => observer.disconnect();
  }, []);

  return theme;
}

/* -----------------------------------------------------------------------
   NyquistGauge — SVG frequency bar
   ----------------------------------------------------------------------- */
const GAUGE_W = 700;
const GAUGE_H = 72;
const PAD = 60;
const BAR_Y = 40;
const BAR_H = 10;

function NyquistGauge({ samplingInfo, theme }) {
  const isDark = theme === 'dark';

  if (!samplingInfo) return null;

  const {
    sampling_frequency: fs,
    nyquist_frequency: nyquist,
    max_signal_frequency: fmax,
    is_above_nyquist: isSafe,
    margin_hz: margin,
  } = samplingInfo;

  const maxFreq = Math.max(fs * 1.3, fmax * 2.5, 30);
  const toX = (f) => PAD + (f / maxFreq) * (GAUGE_W - 2 * PAD);

  const fmaxX = toX(fmax);
  const nyquistX = toX(nyquist);
  const fsX = toX(fs);

  // Decide label positions to avoid overlap
  const fmaxLabel = { x: fmaxX, anchor: 'middle', above: true };
  const nyquistLabel = { x: nyquistX, anchor: 'middle', above: false };

  // If fmax and nyquist markers are too close, stagger labels
  const tooClose = Math.abs(fmaxX - nyquistX) < 55;

  const statusColor = isSafe ? '#10b981' : '#ef4444';
  const absMargin = Math.abs(margin ?? 0).toFixed(1);
  const statusText = isSafe
    ? `SAFE: ${absMargin} Hz margin above Nyquist`
    : `ALIASING: fmax exceeds fs/2 by ${absMargin} Hz`;

  return (
    <div className="sr-nyquist-gauge">
      <svg
        viewBox={`0 0 ${GAUGE_W} ${GAUGE_H}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Background bar */}
        <rect
          x={PAD} y={BAR_Y}
          width={GAUGE_W - 2 * PAD} height={BAR_H}
          rx={BAR_H / 2}
          fill={isDark ? '#1e293b' : '#e2e8f0'}
        />

        {/* Safe zone fill: 0 to min(fmax, nyquist) */}
        <rect
          x={PAD} y={BAR_Y}
          width={Math.max(0, toX(Math.min(fmax, nyquist)) - PAD)}
          height={BAR_H}
          rx={BAR_H / 2}
          fill="rgba(16, 185, 129, 0.25)"
        />

        {/* Aliasing danger zone: nyquist to fmax */}
        {!isSafe && (
          <rect
            x={nyquistX} y={BAR_Y - 3}
            width={Math.max(0, fmaxX - nyquistX)}
            height={BAR_H + 6}
            rx={3}
            fill="rgba(239, 68, 68, 0.18)"
            stroke="rgba(239, 68, 68, 0.35)"
            strokeWidth={1}
          />
        )}

        {/* Marker: fmax */}
        <line
          x1={fmaxX} y1={BAR_Y - 12} x2={fmaxX} y2={BAR_Y + BAR_H + 4}
          stroke="#f59e0b" strokeWidth={2}
        />
        <text
          x={fmaxLabel.x}
          y={tooClose ? BAR_Y - 16 : BAR_Y - 16}
          textAnchor={fmaxLabel.anchor}
          fontSize="9.5" fill="#f59e0b" fontWeight="600"
          fontFamily="'Fira Code', monospace"
        >
          fmax={fmax} Hz
        </text>

        {/* Marker: fs/2 (Nyquist) */}
        <line
          x1={nyquistX} y1={BAR_Y - 12} x2={nyquistX} y2={BAR_Y + BAR_H + 4}
          stroke={statusColor} strokeWidth={2.5}
        />
        <text
          x={nyquistLabel.x}
          y={tooClose ? BAR_Y + BAR_H + 16 : BAR_Y + BAR_H + 16}
          textAnchor={nyquistLabel.anchor}
          fontSize="9.5" fill={statusColor} fontWeight="600"
          fontFamily="'Fira Code', monospace"
        >
          fs/2={nyquist} Hz
        </text>

        {/* Marker: fs (lighter, dashed) */}
        <line
          x1={fsX} y1={BAR_Y - 6} x2={fsX} y2={BAR_Y + BAR_H + 4}
          stroke="#8b5cf6" strokeWidth={1.5}
          strokeDasharray="4,3"
        />
        <text
          x={fsX} y={BAR_Y + BAR_H + 16}
          textAnchor="middle"
          fontSize="8.5" fill="#8b5cf6"
          fontFamily="'Fira Code', monospace"
        >
          fs={fs}
        </text>

        {/* Status message */}
        <text
          x={GAUGE_W / 2} y={12}
          textAnchor="middle"
          fontSize="10.5" fill={statusColor} fontWeight="600"
          fontFamily="Inter, sans-serif"
        >
          {statusText}
        </text>
      </svg>
    </div>
  );
}

/* -----------------------------------------------------------------------
   Info Cards — 4 key metrics
   ----------------------------------------------------------------------- */
function SamplingInfoCards({ samplingInfo }) {
  if (!samplingInfo) return null;

  const {
    sampling_frequency: fs,
    nyquist_frequency: nyquist,
    max_signal_frequency: fmax,
    nyquist_ratio: ratio,
    num_samples,
    is_above_nyquist: isSafe,
  } = samplingInfo;

  const ratioColor = isSafe ? '#10b981' : '#ef4444';
  const ratioText = ratio >= 10 ? `${ratio.toFixed(0)}x` : `${ratio.toFixed(1)}x`;

  return (
    <div className="sr-info-row">
      <div className="sr-info-card" style={{ borderLeftColor: '#3b82f6' }}>
        <span className="sr-card-label">Sampling Rate</span>
        <span className="sr-card-value" style={{ color: '#3b82f6' }}>{fs} Hz</span>
        <span className="sr-card-note">N = {num_samples} samples</span>
      </div>

      <div className="sr-info-card" style={{ borderLeftColor: '#f59e0b' }}>
        <span className="sr-card-label">Max Signal Freq</span>
        <span className="sr-card-value" style={{ color: '#f59e0b' }}>{fmax} Hz</span>
        <span className="sr-card-note">Highest component</span>
      </div>

      <div className="sr-info-card" style={{ borderLeftColor: isSafe ? '#10b981' : '#ef4444' }}>
        <span className="sr-card-label">Nyquist Freq</span>
        <span className="sr-card-value" style={{ color: isSafe ? '#10b981' : '#ef4444' }}>
          {nyquist} Hz
        </span>
        <span className="sr-card-note">fs/2 — the limit</span>
      </div>

      <div className="sr-info-card" style={{ borderLeftColor: ratioColor }}>
        <span className="sr-card-label">Nyquist Ratio</span>
        <span className="sr-card-value" style={{ color: ratioColor }}>{ratioText}</span>
        <span className="sr-card-note">
          {isSafe ? 'fs/2 > fmax (safe)' : 'fs/2 < fmax (aliased!)'}
        </span>
      </div>
    </div>
  );
}

/* -----------------------------------------------------------------------
   Reconstruction quality badges
   ----------------------------------------------------------------------- */
function ReconstructionBadges({ quality, currentParams }) {
  if (!quality) return null;

  const methods = [
    { key: 'zoh', color: '#f59e0b', paramKey: 'show_zoh' },
    { key: 'linear', color: '#10b981', paramKey: 'show_linear' },
    { key: 'sinc', color: '#8b5cf6', paramKey: 'show_sinc' },
  ];

  const active = methods.filter(m => currentParams?.[m.paramKey]);
  if (active.length === 0) return null;

  return (
    <div className="sr-recon-badges">
      {active.map(({ key, color }) => {
        const info = quality[key];
        if (!info) return null;
        const qClass = `sr-quality--${info.quality.toLowerCase()}`;
        return (
          <span key={key} className="sr-recon-badge" style={{ borderColor: color }}>
            <span className="sr-recon-method" style={{ color }}>{info.label}</span>
            <span className={`sr-recon-quality ${qClass}`}>{info.quality}</span>
          </span>
        );
      })}
    </div>
  );
}

/* -----------------------------------------------------------------------
   SRPlot — themed Plotly wrapper
   ----------------------------------------------------------------------- */
function SRPlot({ plot, theme, height = 320 }) {
  const isDark = theme === 'dark';

  const layout = useMemo(() => ({
    title: {
      text: plot.title || '',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 14 },
      x: 0.5,
      xanchor: 'center',
    },
    paper_bgcolor: isDark ? '#0f172a' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#1e293b' : '#f8fafc',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      size: 12,
    },
    xaxis: {
      ...plot.layout?.xaxis,
      gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      title: {
        text: plot.layout?.xaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    yaxis: {
      ...plot.layout?.yaxis,
      gridcolor: isDark ? 'rgba(71,85,105,0.4)' : 'rgba(100,116,139,0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148,163,184,0.5)' : 'rgba(100,116,139,0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      title: {
        text: plot.layout?.yaxis?.title || '',
        font: { color: isDark ? '#94a3b8' : '#334155', size: 12 },
      },
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 11 },
      bgcolor: isDark ? 'rgba(30,41,59,0.9)' : 'rgba(255,255,255,0.9)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
      ...plot.layout?.legend,
    },
    shapes: plot.layout?.shapes,
    annotations: plot.layout?.annotations?.map(a => ({
      ...a,
      font: {
        ...a.font,
        color: isDark ? a.font?.color : a.font?.color,
      },
    })),
    margin: { t: 45, r: 25, b: 55, l: 60 },
    height,
    autosize: true,
    showlegend: true,
    datarevision: `${plot.id}-${plot.title}-${Date.now()}`,
    uirevision: plot.id,
  }), [plot, isDark, height]);

  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
  };

  return (
    <div className="sr-plot-card">
      <Plot
        data={plot.data || []}
        layout={layout}
        config={config}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

/* -----------------------------------------------------------------------
   Main Component
   ----------------------------------------------------------------------- */
function SamplingReconstructionViewer({ metadata, plots, currentParams }) {
  const theme = useTheme();

  if (!plots || plots.length === 0) {
    return (
      <div className="sr-viewer">
        <div className="sr-viewer-empty">
          <p>Loading Sampling & Reconstruction simulation...</p>
        </div>
      </div>
    );
  }

  const samplingInfo = metadata?.sampling_info;
  const quality = metadata?.reconstruction_quality;

  const samplingPlot = plots.find(p => p.id === 'sampling');
  const spectrumPlot = plots.find(p => p.id === 'spectrum');
  const reconstructionPlot = plots.find(p => p.id === 'reconstruction');
  const errorPlot = plots.find(p => p.id === 'error');

  const hasReconData = reconstructionPlot && reconstructionPlot.data?.length > 0;

  return (
    <div className="sr-viewer">
      {/* 1. Nyquist Gauge */}
      <NyquistGauge samplingInfo={samplingInfo} theme={theme} />

      {/* 2. Info cards */}
      <SamplingInfoCards samplingInfo={samplingInfo} />

      {/* 3. Dual plots: Time + Frequency */}
      <div className="sr-dual-plots">
        {samplingPlot && (
          <div className="sr-plot-half">
            <SRPlot plot={samplingPlot} theme={theme} height={340} />
          </div>
        )}
        {spectrumPlot && (
          <div className="sr-plot-half">
            <SRPlot plot={spectrumPlot} theme={theme} height={340} />
          </div>
        )}
      </div>

      {/* 4. Reconstruction comparison */}
      {hasReconData && (
        <div className="sr-reconstruction-section">
          <ReconstructionBadges quality={quality} currentParams={currentParams} />
          <SRPlot plot={reconstructionPlot} theme={theme} height={300} />
        </div>
      )}

      {/* 5. Error plot */}
      {errorPlot && errorPlot.data?.length > 0 && (
        <div className="sr-error-row">
          <SRPlot plot={errorPlot} theme={theme} height={250} />
        </div>
      )}
    </div>
  );
}

export default SamplingReconstructionViewer;
