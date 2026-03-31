/**
 * ODELaplaceViewer Component
 *
 * Custom viewer for the ODE Solver via Laplace Transform.
 * Walks through: original ODE → take L{} → solve for Y(s) → partial fractions
 * → inverse Laplace → final y(t) solution. Supports classical method comparison.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Plot from 'react-plotly.js';

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

// ── SystemInfoBadge ──────────────────────────────────────────────────────────

function SystemInfoBadge({ systemInfo, odeText }) {
  if (!systemInfo) return null;

  const { poles, is_stable, order } = systemInfo;
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

  return (
    <div className="ode-info-badge">
      <div className="ode-badge-row">
        <span className="ode-badge-label">ODE</span>
        <span className="ode-badge-value ode-badge-eq">{odeText || '—'}</span>
      </div>
      <div className="ode-badge-row">
        <span className="ode-badge-label">Order</span>
        <span className="ode-badge-value">{order}</span>
        <span className="ode-badge-pill" style={{
          background: poleType === 'Complex Conjugate' ? 'rgba(124,58,237,0.2)' :
            poleType === 'Repeated' ? 'rgba(245,158,11,0.2)' : 'rgba(20,184,166,0.2)',
          color: poleType === 'Complex Conjugate' ? '#a78bfa' :
            poleType === 'Repeated' ? '#fbbf24' : '#14b8a6',
        }}>
          {poleType}
        </span>
        <span className="ode-badge-pill" style={{
          background: is_stable ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
          color: is_stable ? '#34d399' : '#f87171',
        }}>
          {is_stable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>
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

              {/* Step 1: Term-by-term transforms */}
              {step.step === 1 && step.details?.term_transforms && (
                <div className="ode-transform-table">
                  {step.details.term_transforms.map((t, j) => (
                    <div key={j} className="ode-transform-row">
                      <span className="ode-transform-property">{t.property}</span>
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
            </div>
          </div>
        ))}
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
      </div>
      <div className="ode-compare-summary">
        {classical.summary}
      </div>
    </div>
  );
}

// ── PlotWrapper ──────────────────────────────────────────────────────────────

function PlotWrapper({ plotData, theme, height = 280 }) {
  if (!plotData) return null;

  const isDark = theme === 'dark';
  const backendUiRevision = plotData.layout?.uirevision;

  const layout = {
    ...plotData.layout,
    paper_bgcolor: isDark ? 'rgba(0,0,0,0)' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? 'rgba(0,0,0,0)' : '#f8fafc',
    font: {
      ...(plotData.layout?.font || {}),
      color: isDark ? '#f1f5f9' : '#1e293b',
    },
    autosize: true,
    height,
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
        style={{ width: '100%', height: `${height}px` }}
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

  const currentStep = metadata?.current_step ?? 0;
  const maxStep = metadata?.max_step ?? 5;
  const steps = metadata?.solution_steps ?? [];
  const allTitles = metadata?.all_step_titles ?? [];
  const systemInfo = metadata?.system_info;
  const odeText = metadata?.ode_text;
  const classical = metadata?.classical_solution;

  // Plot lookup
  const findPlot = useCallback((id) => {
    return plots?.find(p => p.id === id) || null;
  }, [plots]);

  // Action handlers
  const handleNext = useCallback(() => onButtonClick?.('next_step'), [onButtonClick]);
  const handlePrev = useCallback(() => onButtonClick?.('prev_step'), [onButtonClick]);
  const handleShowAll = useCallback(() => onButtonClick?.('show_all'), [onButtonClick]);
  const handleReset = useCallback(() => onButtonClick?.('reset_steps'), [onButtonClick]);

  return (
    <div className="ode-viewer" data-theme={theme}>
      {/* System Info */}
      <SystemInfoBadge systemInfo={systemInfo} odeText={odeText} />

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
            <PlotWrapper plotData={findPlot('pole_zero_splane')} theme={theme} height={300} />
          )}

          {/* Input Signal (always visible) */}
          {findPlot('input_signal') && (
            <PlotWrapper plotData={findPlot('input_signal')} theme={theme} height={200} />
          )}
        </div>
      </div>

      {/* Time Response (visible from step 4+) */}
      {findPlot('time_response') && (
        <div className="ode-response-section">
          <PlotWrapper plotData={findPlot('time_response')} theme={theme} height={300} />
        </div>
      )}

      {/* Classical Method Comparison */}
      {classical && <ComparePanel classical={classical} />}

      <style>{`
        .ode-viewer {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          width: 100%;
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
        }
        .ode-badge-eq {
          font-size: 0.9rem;
          color: var(--accent-color, #00d9ff);
        }
        .ode-badge-pill {
          font-size: 0.68rem;
          padding: 0.15rem 0.55rem;
          border-radius: var(--radius-full, 9999px);
          font-weight: 600;
          letter-spacing: 0.03em;
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
          box-shadow: 0 0 8px rgba(20, 184, 166, 0.5);
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
          background: rgba(0, 217, 255, 0.06);
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
          background: rgba(16, 185, 129, 0.08);
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
          grid-template-columns: 1fr 1fr;
          gap: 0.75rem;
        }
        @media (max-width: 768px) {
          .ode-main-grid {
            grid-template-columns: 1fr;
          }
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
          max-height: 400px;
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
          background: rgba(20, 184, 166, 0.06);
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
          line-height: 1.3;
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
          background: rgba(0, 217, 255, 0.04);
          border-radius: var(--radius-sm, 6px);
          flex-wrap: wrap;
        }
        .ode-pair-s {
          color: var(--accent-color, #00d9ff);
        }
        .ode-pair-arrow {
          color: var(--text-muted, #64748b);
        }
        .ode-pair-t {
          color: var(--primary-color, #14b8a6);
        }
        .ode-pair-ref {
          margin-top: 0.3rem;
          padding: 0.4rem 0.5rem;
          background: rgba(148, 163, 184, 0.04);
          border-radius: var(--radius-sm, 6px);
          border: 1px solid rgba(148, 163, 184, 0.08);
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
          background: rgba(245, 158, 11, 0.05);
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
        }
        .ode-compare-summary {
          font-size: 0.72rem;
          color: var(--text-secondary, #94a3b8);
          padding: 0.5rem 0.85rem;
          border-top: 1px solid var(--border-color, #1e293b);
          background: rgba(245, 158, 11, 0.03);
          line-height: 1.5;
        }

        /* ── Light theme overrides ── */
        [data-theme="light"] .ode-info-badge,
        [data-theme="light"] .ode-stepper,
        [data-theme="light"] .ode-detail-panel,
        [data-theme="light"] .ode-compare-panel,
        [data-theme="light"] .ode-plot-wrapper,
        [data-theme="light"] .ode-response-section {
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
      `}</style>
    </div>
  );
}
