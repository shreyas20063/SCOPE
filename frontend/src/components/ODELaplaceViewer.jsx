/**
 * ODELaplaceViewer Component
 *
 * Custom viewer for the ODE Solver via Laplace Transform.
 * Walks through: original ODE → unilateral L{} with initial conditions at 0⁻
 * → A(s)Y(s) − I(s) = B(s)X(s) → partial fractions (zero-state and zero-input)
 * → inverse Laplace → y(t) for t > 0, with the y(0⁻) vs y(0⁺) comparison.
 * Supports classical method comparison.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Plot from 'react-plotly.js';
import katex from 'katex';
import 'katex/dist/katex.min.css';

// ── Theme hook ───────────────────────────────────────────────────────────────

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

/** True when the viewport is phone-sized (legend moves below the plot). */
function useNarrow(maxWidth = 600) {
  const query = `(max-width: ${maxWidth}px)`;
  const [narrow, setNarrow] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia ? window.matchMedia(query).matches : false
  );
  useEffect(() => {
    if (!window.matchMedia) return undefined;
    const mql = window.matchMedia(query);
    const onChange = (e) => setNarrow(e.matches);
    setNarrow(mql.matches);
    if (mql.addEventListener) mql.addEventListener('change', onChange);
    else mql.addListener(onChange);
    return () => {
      if (mql.removeEventListener) mql.removeEventListener('change', onChange);
      else mql.removeListener(onChange);
    };
  }, [query]);
  return narrow;
}

/** Read a design-system CSS variable (falls back when unavailable). */
function cssVar(name, fallback) {
  try {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  } catch {
    return fallback;
  }
}

// ── KaTeX (rendered into a ref; never via innerHTML props) ──────────────────

function Tex({ tex, display = false, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!tex) {
      el.textContent = '';
      return;
    }
    try {
      katex.render(String(tex), el, {
        throwOnError: false,
        displayMode: display,
        trust: false,
        output: 'html',
      });
    } catch {
      el.textContent = String(tex);
    }
  }, [tex, display]);
  return display
    ? <div ref={ref} className={`ode-tex ode-tex--display ${className}`} />
    : <span ref={ref} className={`ode-tex ${className}`} />;
}

// ── Number formatting (typographic minus) ───────────────────────────────────

function fmtNum(x) {
  if (x === null || x === undefined || Number.isNaN(Number(x))) return '—';
  const v = Number(x);
  let s;
  if (Math.abs(v - Math.round(v)) < 1e-9 && Math.abs(v) < 1e9) s = String(Math.round(v));
  else s = String(Number(v.toPrecision(4)));
  if (s === '-0') s = '0';
  return s.replace(/-/g, '−'); // every hyphen, including an exponent's (1e-7)
}

function fmtSigned(x) {
  const s = fmtNum(x);
  return s.startsWith('−') ? s : `+${s}`;
}

// ── SystemInfoBadge ──────────────────────────────────────────────────────────

const STABILITY_LABEL = {
  stable: 'STABLE',
  marginally_stable: 'MARGINALLY STABLE',
  unstable: 'UNSTABLE',
};

function SystemInfoBadge({ systemInfo, odeText, ic, warnings }) {
  if (!systemInfo) return null;

  const { poles, is_stable, order } = systemInfo;
  const stability = systemInfo.stability || (is_stable ? 'stable' : 'unstable');
  const numPoles = poles?.length || 0;

  let poleType = 'None';
  if (numPoles > 0) {
    const hasComplex = poles.some(p => Math.abs(p.imag) > 1e-10);
    const realPoles = poles.filter(p => Math.abs(p.imag) < 1e-10);
    const uniqueReals = [...new Set(realPoles.map(p => p.real.toFixed(6)))];
    const hasRepeated = uniqueReals.length < realPoles.length;

    if (hasComplex) poleType = 'Complex Conjugate';
    else if (hasRepeated) poleType = 'Repeated';
    else poleType = 'Real Distinct';
  }
  const poleClass = poleType === 'Complex Conjugate' ? 'complex'
    : poleType === 'Repeated' ? 'repeated' : 'real';

  let icText = '—';
  if (ic) {
    if (ic.order === 0) icText = 'none (order 0)';
    else if (ic.all_zero) icText = 'initial rest: all zero at t = 0⁻';
    else icText = ic.labels_used.map((lab, j) => `${lab} = ${fmtNum(ic.ics_used[j])}`).join(',  ');
  }

  return (
    <div className="ode-info-badge">
      <div className="ode-badge-row">
        <span className="ode-badge-label">ODE</span>
        <span className="ode-badge-value ode-badge-eq">{odeText || '—'}</span>
      </div>
      <div className="ode-badge-row">
        <span className="ode-badge-label">Order</span>
        <span className="ode-badge-value">{order}</span>
        <span className={`ode-badge-pill ode-pill--${poleClass}`}>{poleType}</span>
        <span className={`ode-badge-pill ode-pill--${stability}`}>
          {STABILITY_LABEL[stability] || stability}
        </span>
      </div>
      <div className="ode-badge-row">
        <span className="ode-badge-label">ICs</span>
        <span className="ode-badge-value ode-badge-ics">{icText}</span>
      </div>
      {ic?.note && <div className="ode-badge-note">{ic.note}</div>}
      {warnings?.map((w, i) => (
        <div key={i} className="ode-badge-warning" role="alert">{w}</div>
      ))}
    </div>
  );
}

// ── SolutionStepper ──────────────────────────────────────────────────────────

function SolutionStepper({ currentStep, maxStep, steps, allTitles, onNext, onPrev, onShowAll, onReset, isUpdating }) {
  const current = steps?.[steps.length - 1];

  return (
    <div className="ode-stepper">
      <div className="ode-step-dots">
        {allTitles?.map((title, i) => (
          <div
            key={i}
            className={`ode-step-dot ${i <= currentStep ? 'active' : ''} ${i === currentStep ? 'current' : ''}`}
            title={title}
          />
        ))}
      </div>

      {current && (
        <div className="ode-step-content">
          <div className="ode-step-title">
            Step {current.step}: {current.title}
          </div>
          <div className="ode-step-equation">{current.equation}</div>
          {current.description && (
            <div className="ode-step-description">{current.description}</div>
          )}
          {/* Key insight callout */}
          {current.details?.key_insight && (
            <div className="ode-key-insight">
              {current.details.key_insight}
            </div>
          )}
        </div>
      )}

      <div className="ode-step-actions">
        <button className="ode-btn ode-btn-secondary" onClick={onPrev} disabled={isUpdating || currentStep <= 0}>
          ← Prev
        </button>
        <button className="ode-btn ode-btn-primary" onClick={onNext} disabled={isUpdating || currentStep >= maxStep}>
          {currentStep >= maxStep ? 'Complete' : 'Next Step'}
        </button>
        <button className="ode-btn ode-btn-secondary" onClick={onShowAll} disabled={isUpdating || currentStep >= maxStep}>
          Show All
        </button>
        <button className="ode-btn ode-btn-secondary" onClick={onReset} disabled={isUpdating || currentStep <= 0}>
          Reset
        </button>
      </div>
    </div>
  );
}

// ── StepDetailPanel ──────────────────────────────────────────────────────────

function DetailLines({ lines }) {
  if (!lines?.length) return null;
  return (
    <div className="ode-lines">
      {lines.map((ln, j) => (
        <div key={j} className="ode-line">
          {ln.label && <span className="ode-line-label">{ln.label}</span>}
          <span className="ode-line-text">{ln.text}</span>
        </div>
      ))}
    </div>
  );
}

function DetailTex({ items }) {
  if (!items?.length) return null;
  return (
    <div className="ode-tex-list">
      {items.map((it, j) => (
        <div key={j} className="ode-tex-row">
          {it.label && <span className="ode-line-label">{it.label}</span>}
          <Tex tex={it.tex} display />
        </div>
      ))}
    </div>
  );
}

function StepDetailPanel({ steps, currentStep }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="ode-detail-panel">
      <div className="ode-detail-header">Solution Steps</div>
      <div className="ode-detail-steps">
        {steps.map((step) => (
          <div
            key={step.step}
            className={`ode-detail-step ${step.step === currentStep ? 'ode-detail-step--current' : ''}`}
          >
            <div className="ode-detail-step-num">{step.step}</div>
            <div className="ode-detail-step-body">
              <div className="ode-detail-step-title">{step.title}</div>
              <div className="ode-detail-step-eq">{step.equation}</div>
              {step.description && (
                <div className="ode-detail-step-desc">{step.description}</div>
              )}

              {/* Typeset key equations (unilateral transform, I(s), IVT) */}
              <DetailTex items={step.details?.tex} />

              {/* Step 1: Term-by-term transforms with the 0⁻ initial-condition terms */}
              {step.step === 1 && step.details?.term_transforms && (
                <div className="ode-transform-table">
                  {step.details.term_transforms.map((t, j) => (
                    <div key={j} className="ode-transform-row">
                      <span className="ode-transform-property">{t.property}</span>
                    </div>
                  ))}
                  {step.details.rhs_properties?.map((p, j) => (
                    <div key={`rhs-${j}`} className="ode-transform-row">
                      <span className="ode-transform-property">{p}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Step 3: PFE algebra */}
              {step.step === 3 && step.details?.algebra_steps && (
                <div className="ode-algebra-steps">
                  {step.details.algebra_steps.map((a, j) => (
                    <div key={j} className="ode-algebra-line">
                      {a.explanation}
                    </div>
                  ))}
                </div>
              )}

              {/* Step 4: Laplace pairs */}
              {step.step === 4 && step.details?.pairs && (
                <div className="ode-pairs-table">
                  {step.details.pairs.map((pair, j) => (
                    <div key={j} className="ode-pair-row">
                      <span className="ode-pair-s">{pair.s_domain}</span>
                      <span className="ode-pair-arrow">→</span>
                      <span className="ode-pair-t">{pair.time_domain}</span>
                    </div>
                  ))}
                  <div className="ode-pair-ref">
                    <div className="ode-pair-ref-title">Reference Table:</div>
                    {step.details.table_reference?.map((ref, j) => (
                      <div key={j} className="ode-pair-ref-row">
                        {ref.s_form} ↔ {ref.t_form}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Zero-state / zero-input parts, I(s), 0⁻ → 0⁺ values */}
              <DetailLines lines={step.details?.lines} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Response view toggle ────────────────────────────────────────────────────

const VIEW_OPTIONS = [
  { value: 'total', label: 'Total y(t)' },
  { value: 'decomposition', label: 'Zero-input + zero-state' },
];

function ResponseToggle({ value, onChange, disabled }) {
  return (
    <div className="ode-toggle" role="group" aria-label="y(t) plot view">
      {VIEW_OPTIONS.map(opt => (
        <button
          key={opt.value}
          type="button"
          className={`ode-toggle-btn ${value === opt.value ? 'active' : ''}`}
          aria-pressed={value === opt.value}
          onClick={() => onChange(opt.value)}
          disabled={disabled}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ── Initial values: 0⁻ vs 0⁺ ────────────────────────────────────────────────

function InitialValuesPanel({ ic }) {
  if (!ic) return null;
  const {
    order, initial_values: values, jump_text: jumpText, ivt_tex: ivtTex,
    explanation, impulse_text: impulseText, cancellations, zi_cancellations: ziCancellations,
  } = ic;

  return (
    <div className="ode-ic-panel">
      <div className="ode-ic-header">Initial values: t = 0⁻ vs t = 0⁺</div>
      <div className="ode-ic-body">
        {order > 0 && values?.length > 0 && (
          <div className="ode-ic-table-wrap">
            <table className="ode-ic-table">
              <thead>
                <tr>
                  <th scope="col">Signal</th>
                  <th scope="col">t = 0⁻<span className="ode-ic-sub">given</span></th>
                  <th scope="col">t = 0⁺<span className="ode-ic-sub">plotted</span></th>
                  <th scope="col">Jump</th>
                </tr>
              </thead>
              <tbody>
                {values.map(v => (
                  <tr key={v.j} className={v.jump !== 0 ? 'ode-ic-row--jump' : ''}>
                    <th scope="row">{v.minus_label.replace('(0⁻)', '')}</th>
                    <td>{fmtNum(v.minus)}</td>
                    <td>{fmtNum(v.plus)}</td>
                    <td className="ode-ic-jump-cell">{v.jump !== 0 ? fmtSigned(v.jump) : '0'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="ode-ic-notes">
          {jumpText && <p className="ode-ic-text ode-ic-text--strong">{jumpText}</p>}
          {ivtTex && (
            <div className="ode-ic-ivt">
              <span className="ode-line-label">Initial value theorem</span>
              <Tex tex={ivtTex} display />
            </div>
          )}
          {impulseText && <p className="ode-ic-text ode-ic-text--warn">{impulseText}</p>}
          {ziCancellations?.map((c, i) => (
            <p key={`zi-${i}`} className="ode-ic-text">{c.text}</p>
          ))}
          {cancellations?.map((c, i) => (
            <p key={`tot-${i}`} className="ode-ic-text ode-ic-text--warn">{c.text}</p>
          ))}
          {explanation && <p className="ode-ic-text ode-ic-text--muted">{explanation}</p>}
        </div>
      </div>
    </div>
  );
}

// ── ComparePanel ─────────────────────────────────────────────────────────────

function ComparePanel({ classical }) {
  if (!classical) return null;

  return (
    <div className="ode-compare-panel">
      <div className="ode-compare-header">
        Classical Method (Homogeneous + Particular)
      </div>
      <div className="ode-compare-steps">
        <div className="ode-compare-step">
          <span className="ode-compare-label">1. Characteristic Eq:</span>
          <span className="ode-compare-eq">{classical.characteristic_eq}</span>
        </div>
        <div className="ode-compare-step">
          <span className="ode-compare-label">2. Roots:</span>
          <span className="ode-compare-eq">{classical.roots?.join(', ')}</span>
        </div>
        <div className="ode-compare-step">
          <span className="ode-compare-label">3. Homogeneous:</span>
          <span className="ode-compare-eq">y_h = {classical.homogeneous_form}</span>
        </div>
        <div className="ode-compare-step">
          <span className="ode-compare-label">4. Particular:</span>
          <span className="ode-compare-eq">{classical.particular_form}</span>
        </div>
        {classical.initial_conditions_note && (
          <div className="ode-compare-step">
            <span className="ode-compare-label">5. Constants:</span>
            <span className="ode-compare-eq">{classical.initial_conditions_note}</span>
          </div>
        )}
      </div>
      <div className="ode-compare-summary">
        {classical.summary}
      </div>
    </div>
  );
}

// ── PlotWrapper ──────────────────────────────────────────────────────────────

function PlotWrapper({ plotData, theme, height = 280, narrow = false }) {
  if (!plotData) return null;

  const isDark = theme === 'dark';
  const backendUiRevision = plotData.layout?.uirevision;
  // Axis/legend colours follow the design-system text tokens so tick labels
  // stay readable in light mode (the backend layout is written for dark).
  const textColor = cssVar('--text-primary', isDark ? '#f1f5f9' : '#0c1425');
  const mutedColor = cssVar('--text-secondary', isDark ? '#94a3b8' : '#2d3f5a');
  const gridColor = isDark ? 'rgba(148,163,184,0.1)' : 'rgba(15,23,42,0.08)';
  const zeroColor = isDark ? 'rgba(148,163,184,0.3)' : 'rgba(15,23,42,0.25)';
  const themedAxis = (axis) => (axis ? {
    ...axis,
    color: textColor,
    gridcolor: gridColor,
    zerolinecolor: zeroColor,
  } : axis);

  const layout = {
    ...plotData.layout,
    paper_bgcolor: isDark ? 'rgba(0,0,0,0)' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? 'rgba(0,0,0,0)' : '#f8fafc',
    font: {
      ...(plotData.layout?.font || {}),
      color: textColor,
    },
    xaxis: themedAxis(plotData.layout?.xaxis),
    yaxis: themedAxis(plotData.layout?.yaxis),
    legend: {
      ...(plotData.layout?.legend || {}),
      font: { ...(plotData.layout?.legend?.font || {}), color: mutedColor },
      ...(narrow ? { orientation: 'h', x: 0, xanchor: 'left', y: -0.3, yanchor: 'top' } : {}),
    },
    ...(narrow ? { margin: { ...(plotData.layout?.margin || {}), r: 12, l: 48 } } : {}),
    autosize: true,
    height: narrow ? height + 60 : height,
    uirevision: backendUiRevision,
  };

  return (
    <div className="ode-plot-wrapper">
      <Plot
        data={plotData.data}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          displaylogo: false,
        }}
        style={{ width: '100%', height: `${narrow ? height + 60 : height}px` }}
        useResizeHandler
      />
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function ODELaplaceViewer({
  metadata,
  plots,
  currentParams,
  onParamChange,
  onButtonClick,
  isUpdating,
}) {
  const theme = useTheme();
  const narrow = useNarrow();

  const currentStep = metadata?.current_step ?? 0;
  const maxStep = metadata?.max_step ?? 5;
  const steps = metadata?.solution_steps ?? [];
  const allTitles = metadata?.all_step_titles ?? [];
  const systemInfo = metadata?.system_info;
  const odeText = metadata?.ode_text;
  const classical = metadata?.classical_solution;
  const ic = metadata?.initial_conditions;
  const warnings = metadata?.warnings;
  const responseView = currentParams?.response_view ?? metadata?.response_view ?? 'total';

  // Plot lookup
  const findPlot = useCallback((id) => {
    return plots?.find(p => p.id === id) || null;
  }, [plots]);

  // Action handlers
  const handleNext = useCallback(() => onButtonClick?.('next_step'), [onButtonClick]);
  const handlePrev = useCallback(() => onButtonClick?.('prev_step'), [onButtonClick]);
  const handleShowAll = useCallback(() => onButtonClick?.('show_all'), [onButtonClick]);
  const handleReset = useCallback(() => onButtonClick?.('reset_steps'), [onButtonClick]);
  const handleView = useCallback((v) => onParamChange?.('response_view', v), [onParamChange]);

  const timePlot = findPlot('time_response');

  return (
    <div className="ode-viewer" data-theme={theme}>
      {/* System Info */}
      <SystemInfoBadge systemInfo={systemInfo} odeText={odeText} ic={ic} warnings={warnings} />

      {/* Solution Stepper */}
      <SolutionStepper
        currentStep={currentStep}
        maxStep={maxStep}
        steps={steps}
        allTitles={allTitles}
        onNext={handleNext}
        onPrev={handlePrev}
        onShowAll={handleShowAll}
        onReset={handleReset}
        isUpdating={isUpdating}
      />

      {/* Main content area */}
      <div className="ode-main-grid">
        {/* Left: Step Detail Panel */}
        <div className="ode-detail-section">
          <StepDetailPanel
            steps={steps}
            currentStep={currentStep}
          />
        </div>

        {/* Right: Plots */}
        <div className="ode-plots-section">
          {/* Pole-Zero Map (visible from step 2+) */}
          {findPlot('pole_zero_splane') && (
            <PlotWrapper plotData={findPlot('pole_zero_splane')} theme={theme} height={300} narrow={narrow} />
          )}

          {/* Input Signal (always visible) */}
          {findPlot('input_signal') && (
            <PlotWrapper plotData={findPlot('input_signal')} theme={theme} height={200} narrow={narrow} />
          )}
        </div>
      </div>

      {/* Time Response (visible from step 4+) */}
      {timePlot && (
        <div className="ode-response-section">
          <div className="ode-response-header">
            <span className="ode-response-title">y(t) for t &gt; 0</span>
            <ResponseToggle value={responseView} onChange={handleView} disabled={!onParamChange} />
          </div>
          <PlotWrapper plotData={timePlot} theme={theme} height={300} narrow={narrow} />
        </div>
      )}

      {/* y(0⁻) vs y(0⁺), IVT, impulses */}
      {timePlot && <InitialValuesPanel ic={ic} />}

      {/* Classical Method Comparison */}
      {classical && <ComparePanel classical={classical} />}

      <style>{`
        .ode-viewer {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          width: 100%;
          min-width: 0;
        }
        /* Thin, theme-coloured scrollbars for the horizontally scrolling equations */
        .ode-step-equation,
        .ode-detail-step-eq,
        .ode-tex--display,
        .ode-ic-table-wrap {
          scrollbar-width: thin;
          scrollbar-color: var(--border-hover, #334155) transparent;
        }
        .ode-step-equation::-webkit-scrollbar,
        .ode-detail-step-eq::-webkit-scrollbar,
        .ode-tex--display::-webkit-scrollbar,
        .ode-ic-table-wrap::-webkit-scrollbar {
          height: 4px;
        }
        .ode-step-equation::-webkit-scrollbar-thumb,
        .ode-detail-step-eq::-webkit-scrollbar-thumb,
        .ode-tex--display::-webkit-scrollbar-thumb,
        .ode-ic-table-wrap::-webkit-scrollbar-thumb {
          background: var(--border-hover, #334155);
          border-radius: var(--radius-full, 9999px);
        }

        /* ── Info Badge ── */
        .ode-info-badge {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
          padding: 0.6rem 0.85rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
        }
        .ode-badge-row {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-wrap: wrap;
          min-width: 0;
        }
        .ode-badge-label {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #64748b);
          font-weight: 600;
          min-width: 35px;
        }
        .ode-badge-value {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-size: 0.82rem;
          color: var(--text-primary, #f1f5f9);
          min-width: 0;
          overflow-wrap: anywhere;
        }
        .ode-badge-eq {
          font-size: 0.9rem;
          color: var(--accent-color, #00d9ff);
        }
        .ode-badge-ics {
          color: var(--text-primary, #f1f5f9);
        }
        .ode-badge-pill {
          font-size: 0.68rem;
          padding: 0.15rem 0.55rem;
          border-radius: var(--radius-full, 9999px);
          font-weight: 600;
          letter-spacing: 0.03em;
        }
        .ode-pill--real {
          background: color-mix(in srgb, var(--primary-color, #14b8a6) 20%, transparent);
          color: var(--primary-color, #14b8a6);
        }
        .ode-pill--complex {
          background: color-mix(in srgb, var(--accent-purple, #7c3aed) 22%, transparent);
          color: color-mix(in srgb, var(--accent-purple, #7c3aed) 60%, var(--text-primary, #f1f5f9));
        }
        .ode-pill--repeated,
        .ode-pill--marginally_stable {
          background: color-mix(in srgb, var(--warning-color, #f59e0b) 20%, transparent);
          color: var(--warning-color, #f59e0b);
        }
        .ode-pill--stable {
          background: color-mix(in srgb, var(--success-color, #10b981) 20%, transparent);
          color: var(--success-color, #10b981);
        }
        .ode-pill--unstable {
          background: color-mix(in srgb, var(--error-color, #ef4444) 20%, transparent);
          color: var(--error-color, #ef4444);
        }
        .ode-badge-note {
          font-size: 0.72rem;
          color: var(--text-secondary, #94a3b8);
          padding-left: calc(35px + 0.5rem);
        }
        .ode-badge-warning {
          font-size: 0.72rem;
          color: var(--warning-color, #f59e0b);
          background: color-mix(in srgb, var(--warning-color, #f59e0b) 10%, transparent);
          border-left: 3px solid var(--warning-color, #f59e0b);
          border-radius: var(--radius-sm, 6px);
          padding: 0.3rem 0.5rem;
        }

        /* ── Stepper ── */
        .ode-stepper {
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
          padding: 0.75rem 1rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          min-width: 0;
        }
        .ode-step-content {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
          min-width: 0;
        }
        .ode-step-dots {
          display: flex;
          gap: 0.4rem;
          align-items: center;
        }
        .ode-step-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--border-color, #1e293b);
          transition: background var(--transition-fast, 150ms), transform var(--transition-fast, 150ms);
        }
        .ode-step-dot.active {
          background: var(--primary-color, #14b8a6);
        }
        .ode-step-dot.current {
          transform: scale(1.3);
          box-shadow: 0 0 8px color-mix(in srgb, var(--primary-color, #14b8a6) 50%, transparent);
        }
        .ode-step-title {
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
        }
        .ode-step-equation {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-size: 0.85rem;
          color: var(--accent-color, #00d9ff);
          padding: 0.4rem 0.7rem;
          background: color-mix(in srgb, var(--accent-color, #00d9ff) 6%, transparent);
          border-radius: var(--radius-sm, 6px);
          border-left: 3px solid var(--accent-color, #00d9ff);
          overflow-x: auto;
          white-space: nowrap;
        }
        .ode-step-description {
          font-size: 0.75rem;
          color: var(--text-secondary, #94a3b8);
          line-height: 1.4;
        }
        .ode-key-insight {
          font-size: 0.75rem;
          color: var(--success-color, #10b981);
          background: color-mix(in srgb, var(--success-color, #10b981) 8%, transparent);
          padding: 0.4rem 0.6rem;
          border-radius: var(--radius-sm, 6px);
          border-left: 3px solid var(--success-color, #10b981);
          font-style: italic;
        }
        .ode-step-actions {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        /* ── Buttons ── */
        .ode-btn {
          padding: 0.4rem 0.9rem;
          border-radius: var(--radius-md, 8px);
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          border: 1px solid transparent;
          transition: all var(--transition-fast, 150ms);
        }
        .ode-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .ode-btn-primary {
          background: var(--primary-color, #14b8a6);
          color: white;
          border-color: var(--primary-color, #14b8a6);
        }
        .ode-btn-primary:hover:not(:disabled) {
          background: var(--primary-hover, #0d9488);
        }
        .ode-btn-secondary {
          background: transparent;
          color: var(--text-secondary, #94a3b8);
          border-color: var(--border-color, #1e293b);
        }
        .ode-btn-secondary:hover:not(:disabled) {
          border-color: var(--border-hover, #334155);
          color: var(--text-primary, #f1f5f9);
        }

        /* ── Main Grid ── */
        .ode-main-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 0.75rem;
        }
        @media (max-width: 768px) {
          .ode-main-grid {
            grid-template-columns: minmax(0, 1fr);
          }
        }
        .ode-detail-section,
        .ode-plots-section {
          min-width: 0;
        }

        /* ── Detail Panel ── */
        .ode-detail-panel {
          display: flex;
          flex-direction: column;
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
        }
        .ode-detail-header {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--text-muted, #64748b);
          padding: 0.6rem 0.85rem;
          border-bottom: 1px solid var(--border-color, #1e293b);
        }
        .ode-detail-steps {
          display: flex;
          flex-direction: column;
          max-height: 520px;
          overflow-y: auto;
          padding: 0.5rem;
        }
        .ode-detail-steps::-webkit-scrollbar {
          width: 4px;
        }
        .ode-detail-steps::-webkit-scrollbar-thumb {
          background: var(--border-color, #1e293b);
          border-radius: var(--radius-full, 9999px);
        }

        .ode-detail-step {
          display: flex;
          gap: 0.6rem;
          padding: 0.5rem;
          border-radius: var(--radius-md, 8px);
          transition: background var(--transition-fast, 150ms);
        }
        .ode-detail-step--current {
          background: color-mix(in srgb, var(--primary-color, #14b8a6) 6%, transparent);
        }
        .ode-detail-step-num {
          min-width: 22px;
          height: 22px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.68rem;
          font-weight: 700;
          background: var(--border-color, #1e293b);
          color: var(--text-secondary, #94a3b8);
          flex-shrink: 0;
        }
        .ode-detail-step--current .ode-detail-step-num {
          background: var(--primary-color, #14b8a6);
          color: white;
        }
        .ode-detail-step-body {
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
          min-width: 0;
          flex: 1;
        }
        .ode-detail-step-title {
          font-size: 0.72rem;
          font-weight: 600;
          color: var(--text-secondary, #94a3b8);
        }
        .ode-detail-step--current .ode-detail-step-title {
          color: var(--text-primary, #f1f5f9);
        }
        .ode-detail-step-eq {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-size: 0.75rem;
          color: var(--accent-color, #00d9ff);
          white-space: nowrap;
          overflow-x: auto;
        }
        .ode-detail-step-desc {
          font-size: 0.68rem;
          color: var(--text-muted, #64748b);
          line-height: 1.35;
        }

        /* ── Typeset equations / detail lines ── */
        .ode-tex-list,
        .ode-lines {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
          margin-top: 0.3rem;
        }
        .ode-tex-row {
          display: flex;
          flex-direction: column;
          gap: 0.1rem;
          min-width: 0;
        }
        .ode-tex--display {
          overflow-x: auto;
          overflow-y: hidden;
          max-width: 100%;
          color: var(--text-primary, #f1f5f9);
          font-size: 0.78rem;
          padding: 0.1rem 0;
        }
        .ode-tex--display .katex-display {
          margin: 0.15rem 0;
          text-align: left;
        }
        .ode-tex--display .katex-display > .katex {
          text-align: left;
        }
        .ode-line {
          display: flex;
          flex-direction: column;
          gap: 0.05rem;
          min-width: 0;
        }
        .ode-line-label {
          font-size: 0.62rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #64748b);
        }
        .ode-line-text {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-size: 0.7rem;
          color: var(--text-secondary, #94a3b8);
          overflow-wrap: anywhere;
          line-height: 1.4;
        }

        /* ── Transform Details ── */
        .ode-transform-table,
        .ode-algebra-steps {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
          margin-top: 0.25rem;
          padding-left: 0.25rem;
        }
        .ode-transform-row,
        .ode-algebra-line {
          font-family: 'Fira Code', monospace;
          font-size: 0.68rem;
          color: var(--text-muted, #64748b);
          overflow-wrap: anywhere;
        }

        /* ── Laplace Pairs ── */
        .ode-pairs-table {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
          margin-top: 0.25rem;
        }
        .ode-pair-row {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-family: 'Fira Code', monospace;
          font-size: 0.7rem;
          padding: 0.25rem 0.4rem;
          background: color-mix(in srgb, var(--accent-color, #00d9ff) 4%, transparent);
          border-radius: var(--radius-sm, 6px);
          flex-wrap: wrap;
          min-width: 0;
        }
        .ode-pair-s {
          color: var(--accent-color, #00d9ff);
          overflow-wrap: anywhere;
        }
        .ode-pair-arrow {
          color: var(--text-muted, #64748b);
        }
        .ode-pair-t {
          color: var(--primary-color, #14b8a6);
          overflow-wrap: anywhere;
        }
        .ode-pair-ref {
          margin-top: 0.3rem;
          padding: 0.4rem 0.5rem;
          background: color-mix(in srgb, var(--text-secondary, #94a3b8) 4%, transparent);
          border-radius: var(--radius-sm, 6px);
          border: 1px solid color-mix(in srgb, var(--text-secondary, #94a3b8) 8%, transparent);
        }
        .ode-pair-ref-title {
          font-size: 0.65rem;
          font-weight: 600;
          color: var(--text-muted, #64748b);
          margin-bottom: 0.2rem;
        }
        .ode-pair-ref-row {
          font-family: 'Fira Code', monospace;
          font-size: 0.65rem;
          color: var(--text-muted, #64748b);
        }

        /* ── Plots Section ── */
        .ode-plots-section {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .ode-plot-wrapper {
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
          border: 1px solid var(--border-color, #1e293b);
          background: var(--surface-color, #131b2e);
        }
        .ode-response-section {
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
          border: 1px solid var(--border-color, #1e293b);
          background: var(--surface-color, #131b2e);
        }
        .ode-response-section .ode-plot-wrapper {
          border: none;
          border-radius: 0;
        }
        .ode-response-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.5rem;
          flex-wrap: wrap;
          padding: 0.5rem 0.75rem;
          border-bottom: 1px solid var(--border-color, #1e293b);
        }
        .ode-response-title {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--text-muted, #64748b);
        }

        /* ── Segmented toggle ── */
        .ode-toggle {
          display: inline-flex;
          border: 1px solid var(--border-color, #1e293b);
          border-radius: var(--radius-md, 8px);
          overflow: hidden;
          max-width: 100%;
        }
        .ode-toggle-btn {
          padding: 0.35rem 0.75rem;
          font-size: 0.74rem;
          font-weight: 600;
          background: transparent;
          color: var(--text-secondary, #94a3b8);
          border: none;
          cursor: pointer;
          transition: background var(--transition-fast, 150ms), color var(--transition-fast, 150ms);
        }
        .ode-toggle-btn + .ode-toggle-btn {
          border-left: 1px solid var(--border-color, #1e293b);
        }
        .ode-toggle-btn:hover:not(:disabled) {
          color: var(--text-primary, #f1f5f9);
        }
        .ode-toggle-btn.active {
          background: color-mix(in srgb, var(--primary-color, #14b8a6) 18%, transparent);
          color: var(--primary-color, #14b8a6);
        }
        .ode-toggle-btn:focus-visible {
          outline: 2px solid var(--primary-color, #14b8a6);
          outline-offset: -2px;
        }

        /* ── Initial values panel ── */
        .ode-ic-panel {
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
        }
        .ode-ic-header {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--secondary-color, #3b82f6);
          padding: 0.6rem 0.85rem;
          border-bottom: 1px solid var(--border-color, #1e293b);
          background: color-mix(in srgb, var(--secondary-color, #3b82f6) 6%, transparent);
        }
        .ode-ic-body {
          display: grid;
          grid-template-columns: minmax(0, 340px) minmax(0, 1fr);
          gap: 0.75rem 1rem;
          padding: 0.75rem 0.85rem;
          align-items: start;
        }
        @media (max-width: 768px) {
          .ode-ic-body {
            grid-template-columns: minmax(0, 1fr);
          }
        }
        .ode-ic-table-wrap {
          overflow-x: auto;
          min-width: 0;
        }
        .ode-ic-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.76rem;
        }
        .ode-ic-table th,
        .ode-ic-table td {
          padding: 0.35rem 0.5rem;
          border-bottom: 1px solid var(--border-color, #1e293b);
          text-align: right;
          white-space: nowrap;
        }
        .ode-ic-sub {
          display: block;
          font-weight: 500;
          text-transform: none;
          letter-spacing: 0;
          opacity: 0.85;
        }
        .ode-ic-table thead th {
          white-space: normal;
          vertical-align: bottom;
          font-size: 0.64rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: var(--text-muted, #64748b);
        }
        .ode-ic-table th[scope="row"],
        .ode-ic-table thead th:first-child {
          text-align: left;
        }
        .ode-ic-table tbody th {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          color: var(--text-primary, #f1f5f9);
          font-weight: 600;
        }
        .ode-ic-table td {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-variant-numeric: tabular-nums;
          color: var(--text-primary, #f1f5f9);
        }
        .ode-ic-row--jump .ode-ic-jump-cell {
          color: var(--warning-color, #f59e0b);
          font-weight: 700;
        }
        .ode-ic-notes {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
          min-width: 0;
        }
        .ode-ic-text {
          margin: 0;
          font-size: 0.74rem;
          line-height: 1.45;
          color: var(--text-secondary, #94a3b8);
        }
        .ode-ic-text--strong {
          color: var(--text-primary, #f1f5f9);
        }
        .ode-ic-text--warn {
          color: var(--warning-color, #f59e0b);
        }
        .ode-ic-text--muted {
          color: var(--text-muted, #64748b);
          font-size: 0.7rem;
        }
        .ode-ic-ivt {
          display: flex;
          flex-direction: column;
          gap: 0.1rem;
          min-width: 0;
        }

        /* ── Compare Panel ── */
        .ode-compare-panel {
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
        }
        .ode-compare-header {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--warning-color, #f59e0b);
          padding: 0.6rem 0.85rem;
          border-bottom: 1px solid var(--border-color, #1e293b);
          background: color-mix(in srgb, var(--warning-color, #f59e0b) 5%, transparent);
        }
        .ode-compare-steps {
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
          padding: 0.6rem 0.85rem;
        }
        .ode-compare-step {
          display: flex;
          gap: 0.5rem;
          align-items: baseline;
          flex-wrap: wrap;
          min-width: 0;
        }
        .ode-compare-label {
          font-size: 0.72rem;
          font-weight: 600;
          color: var(--text-secondary, #94a3b8);
          white-space: nowrap;
        }
        .ode-compare-eq {
          font-family: 'Fira Code', monospace;
          font-size: 0.75rem;
          color: var(--warning-color, #f59e0b);
          min-width: 0;
          overflow-wrap: anywhere;
        }
        .ode-compare-summary {
          font-size: 0.72rem;
          color: var(--text-secondary, #94a3b8);
          padding: 0.5rem 0.85rem;
          border-top: 1px solid var(--border-color, #1e293b);
          background: color-mix(in srgb, var(--warning-color, #f59e0b) 3%, transparent);
          line-height: 1.5;
        }

        /* ── Light theme overrides ── */
        [data-theme="light"] .ode-info-badge,
        [data-theme="light"] .ode-stepper,
        [data-theme="light"] .ode-detail-panel,
        [data-theme="light"] .ode-compare-panel,
        [data-theme="light"] .ode-plot-wrapper,
        [data-theme="light"] .ode-response-section,
        [data-theme="light"] .ode-ic-panel {
          background: rgba(255, 255, 255, 0.98);
          border-color: rgba(0, 0, 0, 0.08);
        }
        [data-theme="light"] .ode-step-equation,
        [data-theme="light"] .ode-detail-step-eq {
          color: #0891b2;
          background: rgba(8, 145, 178, 0.06);
          border-left-color: #0891b2;
        }
        [data-theme="light"] .ode-badge-eq {
          color: #0891b2;
        }
        [data-theme="light"] .ode-key-insight {
          color: #059669;
          background: rgba(5, 150, 105, 0.06);
          border-left-color: #059669;
        }
        [data-theme="light"] .ode-ic-text--warn,
        [data-theme="light"] .ode-badge-warning,
        [data-theme="light"] .ode-ic-row--jump .ode-ic-jump-cell,
        [data-theme="light"] .ode-compare-eq,
        [data-theme="light"] .ode-pill--repeated,
        [data-theme="light"] .ode-pill--marginally_stable {
          color: #b45309;
        }
      `}</style>
    </div>
  );
}
