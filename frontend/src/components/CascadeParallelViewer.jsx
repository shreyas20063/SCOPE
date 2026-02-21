/**
 * CascadeParallelViewer Component
 *
 * Custom viewer for the Cascade & Parallel Decomposition Workbench.
 * Shows three equivalent forms of a second-order DT system with
 * step-by-step factoring animation, SVG block diagrams, and stem plots.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Plot from 'react-plotly.js';

// ── Theme hook (standard pattern) ──────────────────────────────────────────

function useTheme() {
  const [theme, setTheme] = useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );

  useEffect(() => {
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

// ── Utility: format complex number for display ─────────────────────────────

function fmtComplex(real, imag) {
  if (Math.abs(imag) < 1e-10) return real.toFixed(4);
  const sign = imag >= 0 ? '+' : '-';
  return `${real.toFixed(4)} ${sign} ${Math.abs(imag).toFixed(4)}j`;
}

function fmtPole(real, imag) {
  if (Math.abs(imag) < 1e-10) return real.toFixed(3);
  const sign = imag >= 0 ? '+' : '-';
  return `${real.toFixed(3)}${sign}${Math.abs(imag).toFixed(3)}j`;
}

// ── SystemInfoBadge ────────────────────────────────────────────────────────

function SystemInfoBadge({ systemInfo }) {
  if (!systemInfo) return null;

  const { poles_are_complex, poles_are_repeated, is_stable, pole_magnitudes } = systemInfo;
  const p1r = systemInfo.p1_real;
  const p1i = systemInfo.p1_imag;
  const p2r = systemInfo.p2_real;

  let poleType, poleStr;
  if (poles_are_repeated) {
    poleType = 'Repeated';
    poleStr = `p = ${p1r.toFixed(4)}`;
  } else if (poles_are_complex) {
    poleType = 'Complex Conjugate';
    const r = pole_magnitudes[0];
    const theta = Math.atan2(p1i, p1r);
    poleStr = `r = ${r.toFixed(3)}, θ = ${(theta * 180 / Math.PI).toFixed(1)}°`;
  } else {
    poleType = 'Real Distinct';
    poleStr = `p₁ = ${p1r.toFixed(4)}, p₂ = ${p2r.toFixed(4)}`;
  }

  return (
    <div className="cp-info-badge">
      <div className="cp-badge-row">
        <span className="cp-badge-label">Poles</span>
        <span className="cp-badge-value" style={{ fontFamily: "'Fira Code', monospace" }}>
          {poleStr}
        </span>
      </div>
      <div className="cp-badge-row">
        <span className="cp-badge-label">Type</span>
        <span className="cp-badge-pill" style={{
          background: poles_are_complex ? 'rgba(124,58,237,0.2)' : poles_are_repeated ? 'rgba(245,158,11,0.2)' : 'rgba(20,184,166,0.2)',
          color: poles_are_complex ? '#a78bfa' : poles_are_repeated ? '#fbbf24' : '#14b8a6',
        }}>
          {poleType}
        </span>
        <span className="cp-badge-pill" style={{
          background: is_stable ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
          color: is_stable ? '#34d399' : '#f87171',
        }}>
          {is_stable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>
    </div>
  );
}

// ── DecompositionStepper ───────────────────────────────────────────────────

function DecompositionStepper({ step, steps, onDecompose, onReset, isUpdating }) {
  const current = steps?.[step] || steps?.[0];
  const maxStep = (steps?.length || 5) - 1;

  return (
    <div className="cp-stepper">
      <div className="cp-step-dots">
        {steps?.map((s, i) => (
          <div
            key={i}
            className={`cp-step-dot ${i <= step ? 'active' : ''} ${i === step ? 'current' : ''}`}
            title={s.title}
          />
        ))}
      </div>
      <div className="cp-step-content">
        <div className="cp-step-title">
          Step {step}: {current?.title}
        </div>
        <div className="cp-step-equation">{current?.equation}</div>
        <div className="cp-step-description">{current?.description}</div>
      </div>
      <div className="cp-step-actions">
        <button
          className="cp-btn cp-btn-primary"
          onClick={onDecompose}
          disabled={isUpdating || step >= maxStep}
        >
          {step >= maxStep ? 'Complete' : 'Next Step →'}
        </button>
        <button
          className="cp-btn cp-btn-secondary"
          onClick={onReset}
          disabled={isUpdating || step === 0}
        >
          Reset
        </button>
      </div>
    </div>
  );
}

// ── SVG Block Diagrams ─────────────────────────────────────────────────────

function OriginalBlockDiagram({ a1, a2, isDark }) {
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const lineColor = isDark ? '#14b8a6' : '#0d9488';
  const feedbackColor = isDark ? '#00d9ff' : '#0284c7';
  const blockFill = isDark ? '#1e293b' : '#f1f5f9';
  const blockStroke = isDark ? '#334155' : '#cbd5e1';

  return (
    <svg viewBox="0 0 340 200" className="cp-block-diagram" aria-label="Original direct-form block diagram">
      <defs>
        <marker id="cp-arrow-orig" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={lineColor} />
        </marker>
        <marker id="cp-arrow-fb" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={feedbackColor} />
        </marker>
      </defs>

      {/* x[n] label */}
      <text x="10" y="55" fill={textColor} fontSize="13" fontFamily="'Fira Code', monospace">x[n]</text>
      {/* Input arrow */}
      <line x1="48" y1="50" x2="72" y2="50" stroke={lineColor} strokeWidth="2" markerEnd="url(#cp-arrow-orig)" />

      {/* Adder */}
      <circle cx="85" cy="50" r="12" fill={blockFill} stroke={lineColor} strokeWidth="2" />
      <text x="85" y="54" textAnchor="middle" fill={textColor} fontSize="14" fontWeight="bold">+</text>

      {/* Adder → output */}
      <line x1="97" y1="50" x2="270" y2="50" stroke={lineColor} strokeWidth="2" markerEnd="url(#cp-arrow-orig)" />
      {/* y[n] label */}
      <text x="280" y="55" fill={textColor} fontSize="13" fontFamily="'Fira Code', monospace">y[n]</text>

      {/* Feedback tap from output line */}
      <line x1="220" y1="50" x2="220" y2="100" stroke={feedbackColor} strokeWidth="1.5" />

      {/* Delay block R₁ */}
      <rect x="200" y="88" width="40" height="24" rx="4" fill={blockFill} stroke={blockStroke} strokeWidth="1.5" />
      <text x="220" y="104" textAnchor="middle" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace">z⁻¹</text>

      {/* Gain a1 */}
      <line x1="200" y1="100" x2="150" y2="100" stroke={feedbackColor} strokeWidth="1.5" />
      <rect x="120" y="88" width="30" height="24" rx="4" fill={blockFill} stroke={blockStroke} strokeWidth="1.5" />
      <text x="135" y="104" textAnchor="middle" fill={feedbackColor} fontSize="10" fontWeight="bold">a₁</text>
      {/* a1 value */}
      <text x="135" y="80" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">{a1?.toFixed(2)}</text>

      {/* a1 gain → adder */}
      <line x1="120" y1="100" x2="85" y2="100" stroke={feedbackColor} strokeWidth="1.5" />
      <line x1="85" y1="100" x2="85" y2="62" stroke={feedbackColor} strokeWidth="1.5" markerEnd="url(#cp-arrow-fb)" />

      {/* Second delay from first delay output */}
      <line x1="220" y1="112" x2="220" y2="155" stroke={feedbackColor} strokeWidth="1.5" />
      <rect x="200" y="143" width="40" height="24" rx="4" fill={blockFill} stroke={blockStroke} strokeWidth="1.5" />
      <text x="220" y="159" textAnchor="middle" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace">z⁻¹</text>

      {/* Gain a2 */}
      <line x1="200" y1="155" x2="150" y2="155" stroke={feedbackColor} strokeWidth="1.5" />
      <rect x="120" y="143" width="30" height="24" rx="4" fill={blockFill} stroke={blockStroke} strokeWidth="1.5" />
      <text x="135" y="159" textAnchor="middle" fill={feedbackColor} fontSize="10" fontWeight="bold">a₂</text>
      <text x="135" y="135" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">{a2?.toFixed(2)}</text>

      {/* a2 gain → adder (bend around) */}
      <line x1="120" y1="155" x2="60" y2="155" stroke={feedbackColor} strokeWidth="1.5" />
      <line x1="60" y1="155" x2="60" y2="57" stroke={feedbackColor} strokeWidth="1.5" />
      <line x1="60" y1="57" x2="73" y2="57" stroke={feedbackColor} strokeWidth="1.5" markerEnd="url(#cp-arrow-fb)" />
    </svg>
  );
}

function CascadeBlockDiagram({ p1Real, p1Imag, p2Real, p2Imag, isDark }) {
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const lineColor = '#14b8a6';
  const blockFill = isDark ? '#1e293b' : '#f1f5f9';
  const blockStroke = isDark ? '#334155' : '#cbd5e1';

  const p1Str = fmtPole(p1Real, p1Imag);
  const p2Str = fmtPole(p2Real, p2Imag);

  return (
    <svg viewBox="0 0 380 90" className="cp-block-diagram" aria-label="Cascade form block diagram">
      <defs>
        <marker id="cp-arrow-cas" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={lineColor} />
        </marker>
      </defs>

      {/* Input */}
      <text x="5" y="50" fill={textColor} fontSize="13" fontFamily="'Fira Code', monospace">x[n]</text>
      <line x1="42" y1="45" x2="68" y2="45" stroke={lineColor} strokeWidth="2" markerEnd="url(#cp-arrow-cas)" />

      {/* H1 block */}
      <rect x="70" y="25" width="110" height="40" rx="6" fill={blockFill} stroke={lineColor} strokeWidth="2" />
      <text x="125" y="42" textAnchor="middle" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace">
        1/(1-{p1Str}z⁻¹)
      </text>
      <text x="125" y="56" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">H₁(z)</text>

      {/* Arrow between blocks */}
      <line x1="180" y1="45" x2="208" y2="45" stroke={lineColor} strokeWidth="2" markerEnd="url(#cp-arrow-cas)" />

      {/* H2 block */}
      <rect x="210" y="25" width="110" height="40" rx="6" fill={blockFill} stroke={lineColor} strokeWidth="2" />
      <text x="265" y="42" textAnchor="middle" fill={textColor} fontSize="11" fontFamily="'Fira Code', monospace">
        1/(1-{p2Str}z⁻¹)
      </text>
      <text x="265" y="56" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">H₂(z)</text>

      {/* Output */}
      <line x1="320" y1="45" x2="348" y2="45" stroke={lineColor} strokeWidth="2" markerEnd="url(#cp-arrow-cas)" />
      <text x="350" y="50" fill={textColor} fontSize="13" fontFamily="'Fira Code', monospace">y[n]</text>
    </svg>
  );
}

function ParallelBlockDiagram({ A1Real, A1Imag, p1Real, p1Imag, A2Real, A2Imag, p2Real, p2Imag, isDark }) {
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const line1Color = '#fbbf24';
  const line2Color = '#f472b6';
  const sumColor = '#22d3ee';
  const blockFill = isDark ? '#1e293b' : '#f1f5f9';
  const blockStroke = isDark ? '#334155' : '#cbd5e1';

  const A1Str = fmtPole(A1Real, A1Imag);
  const A2Str = fmtPole(A2Real, A2Imag);
  const p1Str = fmtPole(p1Real, p1Imag);
  const p2Str = fmtPole(p2Real, p2Imag);

  return (
    <svg viewBox="0 0 400 150" className="cp-block-diagram" aria-label="Parallel form block diagram">
      <defs>
        <marker id="cp-arrow-p1" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={line1Color} />
        </marker>
        <marker id="cp-arrow-p2" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={line2Color} />
        </marker>
        <marker id="cp-arrow-sum" markerWidth="7" markerHeight="5" refX="6" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill={sumColor} />
        </marker>
      </defs>

      {/* Input */}
      <text x="5" y="77" fill={textColor} fontSize="13" fontFamily="'Fira Code', monospace">x[n]</text>
      <line x1="42" y1="72" x2="60" y2="72" stroke={isDark ? '#94a3b8' : '#64748b'} strokeWidth="1.5" />

      {/* Split point */}
      <circle cx="60" cy="72" r="3" fill={textColor} />

      {/* Upper branch */}
      <line x1="60" y1="72" x2="60" y2="35" stroke={line1Color} strokeWidth="1.5" />
      <line x1="60" y1="35" x2="90" y2="35" stroke={line1Color} strokeWidth="1.5" markerEnd="url(#cp-arrow-p1)" />
      <rect x="92" y="17" width="140" height="36" rx="6" fill={blockFill} stroke={line1Color} strokeWidth="1.5" />
      <text x="162" y="33" textAnchor="middle" fill={textColor} fontSize="10" fontFamily="'Fira Code', monospace">
        {A1Str}/(1-{p1Str}z⁻¹)
      </text>
      <text x="162" y="46" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">Mode 1</text>
      <line x1="232" y1="35" x2="300" y2="35" stroke={line1Color} strokeWidth="1.5" />

      {/* Lower branch */}
      <line x1="60" y1="72" x2="60" y2="110" stroke={line2Color} strokeWidth="1.5" />
      <line x1="60" y1="110" x2="90" y2="110" stroke={line2Color} strokeWidth="1.5" markerEnd="url(#cp-arrow-p2)" />
      <rect x="92" y="92" width="140" height="36" rx="6" fill={blockFill} stroke={line2Color} strokeWidth="1.5" />
      <text x="162" y="108" textAnchor="middle" fill={textColor} fontSize="10" fontFamily="'Fira Code', monospace">
        {A2Str}/(1-{p2Str}z⁻¹)
      </text>
      <text x="162" y="121" textAnchor="middle" fill={isDark ? '#94a3b8' : '#64748b'} fontSize="9">Mode 2</text>
      <line x1="232" y1="110" x2="300" y2="110" stroke={line2Color} strokeWidth="1.5" />

      {/* Adder */}
      <line x1="300" y1="35" x2="300" y2="60" stroke={line1Color} strokeWidth="1.5" />
      <line x1="300" y1="110" x2="300" y2="85" stroke={line2Color} strokeWidth="1.5" />
      <circle cx="300" cy="72" r="12" fill={blockFill} stroke={sumColor} strokeWidth="2" />
      <text x="300" y="76" textAnchor="middle" fill={textColor} fontSize="14" fontWeight="bold">+</text>

      {/* Output */}
      <line x1="312" y1="72" x2="355" y2="72" stroke={sumColor} strokeWidth="2" markerEnd="url(#cp-arrow-sum)" />
      <text x="358" y="77" fill={textColor} fontSize="13" fontFamily="'Fira Code', monospace">y[n]</text>
    </svg>
  );
}

// ── StemPlot (Plotly wrapper) ──────────────────────────────────────────────

function StemPlot({ plotData, theme, height = 220 }) {
  if (!plotData) return null;

  const isDark = theme === 'dark';

  // Use the backend's uirevision (includes param fingerprint) so zoom resets on data changes
  const backendUiRevision = plotData.layout?.uirevision || plotData.id;

  const layout = {
    ...plotData.layout,
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: {
      family: 'Inter, sans-serif',
      size: 11,
      color: isDark ? '#94a3b8' : '#475569',
    },
    title: {
      ...(plotData.layout?.title || {}),
      font: {
        size: 13,
        color: isDark ? '#f1f5f9' : '#1e293b',
      },
    },
    xaxis: {
      ...plotData.layout?.xaxis,
      gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
      color: isDark ? '#94a3b8' : '#475569',
    },
    yaxis: {
      ...plotData.layout?.yaxis,
      autorange: true,
      gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
      color: isDark ? '#94a3b8' : '#475569',
    },
    legend: {
      ...plotData.layout?.legend,
      bgcolor: isDark ? 'rgba(0,0,0,0.4)' : 'rgba(255,255,255,0.9)',
      font: { size: 10, color: isDark ? '#f1f5f9' : '#1e293b' },
    },
    margin: { t: 40, r: 20, b: 45, l: 50 },
    height,
    datarevision: `${plotData.id}-${plotData.title}-${Date.now()}`,
    uirevision: backendUiRevision,
  };

  return (
    <div className="cp-stem-plot">
      <Plot
        data={plotData.data}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ['autoScale2d', 'lasso2d', 'select2d'],
          displaylogo: false,
        }}
        style={{ width: '100%', height: `${height}px` }}
        useResizeHandler
      />
    </div>
  );
}

// ── FormPanel ──────────────────────────────────────────────────────────────

function FormPanel({ title, visible, color, children }) {
  return (
    <div
      className={`cp-form-panel ${visible ? 'visible' : 'hidden'}`}
      style={{ '--panel-accent': color }}
    >
      <div className="cp-form-panel-header">
        <div className="cp-form-panel-dot" style={{ background: color }} />
        <span>{title}</span>
      </div>
      <div className="cp-form-panel-body">
        {children}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

export default function CascadeParallelViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const theme = useTheme();
  const isDark = theme === 'dark';

  const step = metadata?.decomposition_step ?? 0;
  const steps = metadata?.factoring_steps;
  const info = metadata?.system_info;

  const handleDecompose = useCallback(() => {
    onButtonClick?.('decompose');
  }, [onButtonClick]);

  const handleReset = useCallback(() => {
    onButtonClick?.('reset_decomposition');
  }, [onButtonClick]);

  const findPlot = useCallback((id) => {
    return plots?.find((p) => p.id === id) || null;
  }, [plots]);

  return (
    <div className="cp-viewer" data-theme={theme}>
      {/* Info Badge */}
      <SystemInfoBadge systemInfo={info} />

      {/* Decomposition Stepper */}
      <DecompositionStepper
        step={step}
        steps={steps}
        onDecompose={handleDecompose}
        onReset={handleReset}
        isUpdating={isUpdating}
      />

      {/* Three-panel layout */}
      <div className="cp-panels">
        {/* Original form — always visible */}
        <FormPanel title="Original (Direct Form)" visible={true} color="#3b82f6">
          <OriginalBlockDiagram a1={info?.a1} a2={info?.a2} isDark={isDark} />
          <StemPlot plotData={findPlot('original_response')} theme={theme} />
        </FormPanel>

        {/* Cascade form — visible at step >= 2 */}
        <FormPanel title="Cascade (Series) Form" visible={step >= 2} color="#14b8a6">
          <CascadeBlockDiagram
            p1Real={info?.p1_real} p1Imag={info?.p1_imag}
            p2Real={info?.p2_real} p2Imag={info?.p2_imag}
            isDark={isDark}
          />
          <StemPlot plotData={findPlot('cascade_response')} theme={theme} />
        </FormPanel>

        {/* Parallel form — visible at step >= 3 */}
        <FormPanel title="Parallel (Partial Fraction) Form" visible={step >= 3} color="#22d3ee">
          <ParallelBlockDiagram
            A1Real={info?.A1_real} A1Imag={info?.A1_imag}
            p1Real={info?.p1_real} p1Imag={info?.p1_imag}
            A2Real={info?.A2_real} A2Imag={info?.A2_imag}
            p2Real={info?.p2_real} p2Imag={info?.p2_imag}
            isDark={isDark}
          />
          <StemPlot plotData={findPlot('parallel_response')} theme={theme} />
        </FormPanel>

        {/* Individual modes — visible at step 4 */}
        {step >= 4 && (
          <FormPanel title="Individual Geometric Modes" visible={true} color="#fbbf24">
            <StemPlot plotData={findPlot('individual_modes')} theme={theme} height={260} />
          </FormPanel>
        )}
      </div>

      <style>{`
        .cp-viewer {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          width: 100%;
        }

        /* ── Info Badge ── */
        .cp-info-badge {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          padding: 0.6rem 0.85rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
        }
        .cp-badge-row {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .cp-badge-label {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #64748b);
          font-weight: 600;
        }
        .cp-badge-value {
          font-size: 0.82rem;
          color: var(--text-primary, #f1f5f9);
        }
        .cp-badge-pill {
          font-size: 0.68rem;
          padding: 0.15rem 0.55rem;
          border-radius: var(--radius-full, 9999px);
          font-weight: 600;
          letter-spacing: 0.03em;
        }

        /* ── Stepper ── */
        .cp-stepper {
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
          padding: 0.75rem 1rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
        }
        .cp-step-dots {
          display: flex;
          gap: 0.4rem;
          align-items: center;
        }
        .cp-step-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--border-color, #1e293b);
          transition: background var(--transition-fast, 150ms), transform var(--transition-fast, 150ms);
        }
        .cp-step-dot.active {
          background: var(--primary-color, #14b8a6);
        }
        .cp-step-dot.current {
          transform: scale(1.3);
          box-shadow: 0 0 8px rgba(20, 184, 166, 0.5);
        }
        .cp-step-title {
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
        }
        .cp-step-equation {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-size: 0.82rem;
          color: var(--accent-color, #00d9ff);
          padding: 0.35rem 0.6rem;
          background: rgba(0, 217, 255, 0.06);
          border-radius: var(--radius-sm, 6px);
          border-left: 3px solid var(--accent-color, #00d9ff);
          overflow-x: auto;
          white-space: nowrap;
        }
        .cp-step-description {
          font-size: 0.75rem;
          color: var(--text-secondary, #94a3b8);
          line-height: 1.4;
        }
        .cp-step-actions {
          display: flex;
          gap: 0.5rem;
        }
        .cp-btn {
          padding: 0.4rem 0.9rem;
          border-radius: var(--radius-md, 8px);
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          border: 1px solid transparent;
          transition: all var(--transition-fast, 150ms);
        }
        .cp-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .cp-btn-primary {
          background: var(--primary-color, #14b8a6);
          color: white;
          border-color: var(--primary-color, #14b8a6);
        }
        .cp-btn-primary:hover:not(:disabled) {
          background: var(--primary-hover, #0d9488);
        }
        .cp-btn-secondary {
          background: transparent;
          color: var(--text-secondary, #94a3b8);
          border-color: var(--border-color, #1e293b);
        }
        .cp-btn-secondary:hover:not(:disabled) {
          border-color: var(--border-hover, #334155);
          color: var(--text-primary, #f1f5f9);
        }

        /* ── Panels ── */
        .cp-panels {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .cp-form-panel {
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          overflow: hidden;
          transition: opacity var(--transition-slow, 400ms) ease, max-height var(--transition-slow, 400ms) ease, margin var(--transition-slow, 400ms) ease;
        }
        .cp-form-panel.visible {
          opacity: 1;
          max-height: 700px;
        }
        .cp-form-panel.hidden {
          opacity: 0;
          max-height: 0;
          margin: 0;
          border: none;
        }
        .cp-form-panel-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.55rem 0.85rem;
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
          border-bottom: 1px solid var(--border-color, #1e293b);
        }
        .cp-form-panel-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        .cp-form-panel-body {
          padding: 0.5rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
        }

        /* ── Block Diagrams ── */
        .cp-block-diagram {
          width: 100%;
          max-width: 420px;
          height: auto;
        }

        /* ── Stem Plot ── */
        .cp-stem-plot {
          width: 100%;
        }
        .cp-stem-plot .js-plotly-plot {
          border-radius: var(--radius-md, 8px);
        }

        /* ── Responsive ── */
        @media (min-width: 1200px) {
          .cp-panels {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 0.75rem;
          }
        }
      `}</style>
    </div>
  );
}
