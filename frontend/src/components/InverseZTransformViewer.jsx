/**
 * InverseZTransformViewer Component
 *
 * Custom viewer for the Inverse Z Transform Step-by-Step Solver.
 * Walks through: factor denominator → partial fractions → Z-transform pair
 * matching → assemble h[n]. Supports quiz mode and three solution methods.
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

// ── Utility ──────────────────────────────────────────────────────────────────

function fmtComplex(real, imag) {
  if (Math.abs(imag) < 1e-10) {
    const v = real;
    if (Math.abs(v - Math.round(v)) < 1e-10 && Math.abs(v) < 1e6) {
      return Math.abs(v) >= 1 ? `${Math.round(v)}` : v.toFixed(4);
    }
    return v.toFixed(4);
  }
  const sign = imag >= 0 ? '+' : '−';
  return `${real.toFixed(4)} ${sign} ${Math.abs(imag).toFixed(4)}j`;
}

// ── SystemInfoBadge ──────────────────────────────────────────────────────────

function SystemInfoBadge({ systemInfo }) {
  if (!systemInfo) return null;

  const { poles, zeros, residues, is_stable, roc_regions } = systemInfo;
  const numPoles = poles?.length || 0;

  // Detect pole type
  let poleType = 'None';
  let poleStr = '—';
  if (numPoles > 0) {
    const hasComplex = poles.some(p => Math.abs(p.imag) > 1e-10);
    const mags = poles.map(p => p.magnitude);
    const uniqueMags = [...new Set(mags.map(m => m.toFixed(8)))];
    const hasRepeated = uniqueMags.length < numPoles && !hasComplex;

    if (hasComplex) {
      poleType = 'Complex Conjugate';
      const r = poles[0].magnitude;
      const theta = Math.atan2(poles[0].imag, poles[0].real);
      poleStr = `r = ${r.toFixed(4)}, θ = ${(theta * 180 / Math.PI).toFixed(1)}°`;
    } else if (hasRepeated) {
      poleType = 'Repeated';
      poleStr = `p = ${poles[0].real.toFixed(4)}`;
    } else {
      poleType = 'Real Distinct';
      poleStr = poles.map((p, i) => `p${i + 1}=${p.real.toFixed(4)}`).join(', ');
    }
  }

  return (
    <div className="izt-info-badge">
      <div className="izt-badge-row">
        <span className="izt-badge-label">Poles</span>
        <span className="izt-badge-value">{poleStr}</span>
      </div>
      <div className="izt-badge-row">
        <span className="izt-badge-label">Type</span>
        <span className="izt-badge-pill" style={{
          background: poleType === 'Complex Conjugate' ? 'rgba(124,58,237,0.2)' :
            poleType === 'Repeated' ? 'rgba(245,158,11,0.2)' : 'rgba(20,184,166,0.2)',
          color: poleType === 'Complex Conjugate' ? '#a78bfa' :
            poleType === 'Repeated' ? '#fbbf24' : '#14b8a6',
        }}>
          {poleType}
        </span>
        <span className="izt-badge-pill" style={{
          background: is_stable ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)',
          color: is_stable ? '#34d399' : '#f87171',
        }}>
          {is_stable ? 'STABLE' : 'UNSTABLE'}
        </span>
      </div>
      {residues && residues.length > 0 && (
        <div className="izt-badge-row">
          <span className="izt-badge-label">Residues</span>
          <span className="izt-badge-value">
            {residues.map((r, i) => `R${i + 1}=${fmtComplex(r.real, r.imag)}`).join(', ')}
          </span>
        </div>
      )}
    </div>
  );
}

// ── MethodTabs ───────────────────────────────────────────────────────────────

function MethodTabs({ activeMethod, onMethodChange }) {
  const methods = [
    { id: 'partial_fractions', label: 'A: Partial Fractions' },
    { id: 'long_division', label: 'B: Long Division' },
    { id: 'power_series', label: 'C: Power Series' },
  ];

  return (
    <div className="izt-method-tabs">
      {methods.map(m => (
        <button
          key={m.id}
          className={`izt-method-tab ${activeMethod === m.id ? 'active' : ''}`}
          onClick={() => onMethodChange?.('active_method', m.id)}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}

// ── SolutionStepper ──────────────────────────────────────────────────────────

function SolutionStepper({ currentStep, maxStep, steps, allTitles, onNext, onPrev, onShowAll, onReset, isUpdating }) {
  const current = steps?.[steps.length - 1];

  return (
    <div className="izt-stepper">
      <div className="izt-step-dots">
        {allTitles?.map((title, i) => (
          <div
            key={i}
            className={`izt-step-dot ${i <= currentStep ? 'active' : ''} ${i === currentStep ? 'current' : ''}`}
            title={title}
          />
        ))}
      </div>

      {current && (
        <div className="izt-step-content">
          <div className="izt-step-title">
            Step {current.step}: {current.title}
          </div>
          <div className="izt-step-equation">{current.equation}</div>
          {current.description && (
            <div className="izt-step-description">{current.description}</div>
          )}
        </div>
      )}

      <div className="izt-step-actions">
        <button className="izt-btn izt-btn-secondary" onClick={onPrev} disabled={isUpdating || currentStep <= 0}>
          ← Prev
        </button>
        <button className="izt-btn izt-btn-primary" onClick={onNext} disabled={isUpdating || currentStep >= maxStep}>
          {currentStep >= maxStep ? 'Complete' : 'Next Step'}
        </button>
        <button className="izt-btn izt-btn-secondary" onClick={onShowAll} disabled={isUpdating || currentStep >= maxStep}>
          Show All
        </button>
        <button className="izt-btn izt-btn-secondary" onClick={onReset} disabled={isUpdating || currentStep <= 0}>
          Reset
        </button>
      </div>
    </div>
  );
}

// ── StepDetailPanel ──────────────────────────────────────────────────────────

function StepDetailPanel({ steps, currentStep, activeMethod, methodBSteps, methodCTerms }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="izt-detail-panel">
      <div className="izt-detail-header">Solution Steps</div>
      <div className="izt-detail-steps">
        {steps.map((step, idx) => (
          <div
            key={step.step}
            className={`izt-detail-step ${step.step === currentStep ? 'izt-detail-step--current' : ''}`}
          >
            <div className="izt-detail-step-num">{step.step}</div>
            <div className="izt-detail-step-body">
              <div className="izt-detail-step-title">{step.title}</div>
              <div className="izt-detail-step-eq">{step.equation}</div>
              {step.description && (
                <div className="izt-detail-step-desc">{step.description}</div>
              )}

              {/* Partial fraction algebra details */}
              {step.step === 2 && step.details?.algebra_steps && (
                <div className="izt-algebra-steps">
                  {step.details.algebra_steps.map((a, j) => (
                    <div key={j} className="izt-algebra-line">
                      {a.explanation}
                    </div>
                  ))}
                </div>
              )}

              {/* Z-transform pair details */}
              {step.step === 3 && step.details?.pairs && (
                <div className="izt-pairs-table">
                  {step.details.pairs.map((pair, j) => (
                    <div key={j} className={`izt-pair-row ${pair.causal ? 'causal' : 'anticausal'}`}>
                      <span className="izt-pair-badge">{pair.causal ? 'Causal' : 'Anti-causal'}</span>
                      <span className="izt-pair-eq">{pair.zt_pair}</span>
                      <span className="izt-pair-arrow">→</span>
                      <span className="izt-pair-term">{pair.time_term}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Method B: Long Division */}
      {activeMethod === 'long_division' && methodBSteps && methodBSteps.length > 0 && (
        <div className="izt-method-detail">
          <div className="izt-detail-header">Long Division Coefficients</div>
          <div className="izt-long-div-table">
            {methodBSteps.map((s, i) => (
              <div key={i} className="izt-long-div-row">
                <span className="izt-long-div-eq">{s.equation}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Method C: Power Series */}
      {activeMethod === 'power_series' && methodCTerms && methodCTerms.length > 0 && (
        <div className="izt-method-detail">
          <div className="izt-detail-header">Power Series Terms</div>
          <div className="izt-power-series">
            {methodCTerms.slice(0, 12).map((val, n) => (
              <span key={n} className="izt-ps-term">
                h[{n}] = {typeof val === 'number' ? val.toFixed(4) : val}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── QuizPanel ────────────────────────────────────────────────────────────────

function QuizPanel({ quiz, poles, onCheckQuiz, onNewQuiz, isUpdating }) {
  const [answers, setAnswers] = useState({});

  const handleChange = useCallback((idx, field, value) => {
    setAnswers(prev => ({
      ...prev,
      [idx]: { ...prev[idx], [field]: value },
    }));
  }, []);

  const handleCheck = useCallback(() => {
    onCheckQuiz?.('check_quiz', { answers });
  }, [answers, onCheckQuiz]);

  const handleNew = useCallback(() => {
    setAnswers({});
    onNewQuiz?.('new_quiz');
  }, [onNewQuiz]);

  if (!quiz?.active) {
    return (
      <div className="izt-quiz-panel">
        <div className="izt-quiz-prompt">
          Enter Quiz Mode to test your partial fraction skills!
        </div>
        <button className="izt-btn izt-btn-primary" onClick={handleNew} disabled={isUpdating}>
          Start Quiz
        </button>
      </div>
    );
  }

  return (
    <div className="izt-quiz-panel">
      <div className="izt-quiz-header">
        Guess the residue for each pole:
      </div>
      {poles?.map((pole, i) => {
        const score = quiz.scores?.find(s => s.index === i);
        return (
          <div key={i} className={`izt-quiz-row ${score ? (score.correct ? 'correct' : 'incorrect') : ''}`}>
            <span className="izt-quiz-pole">
              Pole p{i + 1} = {fmtComplex(pole.real, pole.imag)}
            </span>
            <div className="izt-quiz-inputs">
              <label>
                Re:
                <input
                  type="number"
                  step="0.1"
                  value={answers[i]?.real ?? ''}
                  onChange={(e) => handleChange(i, 'real', e.target.value)}
                  disabled={quiz.checked}
                  className="izt-quiz-input"
                />
              </label>
              {Math.abs(pole.imag) > 1e-10 && (
                <label>
                  Im:
                  <input
                    type="number"
                    step="0.1"
                    value={answers[i]?.imag ?? ''}
                    onChange={(e) => handleChange(i, 'imag', e.target.value)}
                    disabled={quiz.checked}
                    className="izt-quiz-input"
                  />
                </label>
              )}
            </div>
            {score && (
              <div className="izt-quiz-feedback">
                {score.correct ? '✓ Correct!' : `✗ Actual: ${fmtComplex(score.actual_real, score.actual_imag)}`}
              </div>
            )}
          </div>
        );
      })}
      <div className="izt-quiz-actions">
        {!quiz.checked ? (
          <button className="izt-btn izt-btn-primary" onClick={handleCheck} disabled={isUpdating}>
            Check Answers
          </button>
        ) : (
          <button className="izt-btn izt-btn-primary" onClick={handleNew} disabled={isUpdating}>
            New Quiz
          </button>
        )}
      </div>
    </div>
  );
}

// ── ROCSelector ──────────────────────────────────────────────────────────────

function ROCSelector({ rocRegions, onROCChange, isDark }) {
  if (!rocRegions || rocRegions.length === 0) return null;

  return (
    <div className="izt-roc-selector">
      <div className="izt-roc-header">Per-Pole ROC Assignment</div>
      {rocRegions.map((region, i) => (
        <div key={i} className="izt-roc-row">
          <span className="izt-roc-pole">
            p{i + 1} = {fmtComplex(region.pole_real, region.pole_imag)}
            <span className="izt-roc-mag">(|p| = {region.pole_magnitude.toFixed(4)})</span>
          </span>
          <div className="izt-roc-toggle">
            <button
              className={`izt-roc-btn ${region.causal ? 'active' : ''}`}
              onClick={() => onROCChange(i, true)}
            >
              Causal
            </button>
            <button
              className={`izt-roc-btn ${!region.causal ? 'active anticausal' : ''}`}
              onClick={() => onROCChange(i, false)}
            >
              Anti-causal
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── StemPlot (Plotly wrapper) ────────────────────────────────────────────────

function StemPlot({ plotData, theme, height = 240 }) {
  if (!plotData) return null;
  const isDark = theme === 'dark';

  const backendUiRevision = plotData.layout?.uirevision || plotData.id;

  // Determine if backend set explicit x/y ranges
  const hasExplicitXRange = !!plotData.layout?.xaxis?.range;
  const hasExplicitYRange = !!plotData.layout?.yaxis?.range && !plotData.layout?.yaxis?.autorange;

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
      font: { size: 13, color: isDark ? '#f1f5f9' : '#1e293b' },
    },
    xaxis: {
      ...plotData.layout?.xaxis,
      autorange: hasExplicitXRange ? false : true,
      gridcolor: isDark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.15)',
      zerolinecolor: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.3)',
      color: isDark ? '#94a3b8' : '#475569',
    },
    yaxis: {
      ...plotData.layout?.yaxis,
      autorange: hasExplicitYRange ? false : true,
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
    <div className="izt-stem-plot">
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

// ── Main Component ───────────────────────────────────────────────────────────

export default function InverseZTransformViewer({
  metadata,
  plots,
  currentParams,
  onParamChange,
  onButtonClick,
  isUpdating,
}) {
  const theme = useTheme();
  const isDark = theme === 'dark';

  const currentStep = metadata?.current_step ?? 0;
  const maxStep = metadata?.max_step ?? 4;
  const steps = metadata?.solution_steps ?? [];
  const allTitles = metadata?.all_step_titles ?? [];
  const systemInfo = metadata?.system_info;
  const activeMethod = metadata?.active_method ?? 'partial_fractions';
  const mode = metadata?.mode ?? 'solve';
  const quiz = metadata?.quiz;
  const rocType = currentParams?.roc_type ?? 'causal';

  // Plot lookup
  const findPlot = useCallback((id) => {
    return plots?.find(p => p.id === id) || null;
  }, [plots]);

  // Action handlers
  const handleNext = useCallback(() => onButtonClick?.('next_step'), [onButtonClick]);
  const handlePrev = useCallback(() => onButtonClick?.('prev_step'), [onButtonClick]);
  const handleShowAll = useCallback(() => onButtonClick?.('show_all'), [onButtonClick]);
  const handleReset = useCallback(() => onButtonClick?.('reset_steps'), [onButtonClick]);

  const handleROCChange = useCallback((poleIndex, causal) => {
    onButtonClick?.('set_roc_region', { pole_index: poleIndex, causal });
  }, [onButtonClick]);

  return (
    <div className="izt-viewer" data-theme={theme}>
      {/* System Info */}
      <SystemInfoBadge systemInfo={systemInfo} />

      {/* Method Tabs */}
      <MethodTabs activeMethod={activeMethod} onMethodChange={onParamChange} />

      {/* Solution Stepper */}
      {mode === 'solve' && (
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
      )}

      {/* Main content area */}
      <div className="izt-main-grid">
        {/* Left: Pole-Zero Map */}
        <div className="izt-pz-section">
          <StemPlot plotData={findPlot('pole_zero_map')} theme={theme} height={320} />

          {/* ROC Selector for custom mode */}
          {rocType === 'custom' && (
            <ROCSelector
              rocRegions={systemInfo?.roc_regions}
              onROCChange={handleROCChange}
              isDark={isDark}
            />
          )}
        </div>

        {/* Right: Detail panel / Quiz */}
        <div className="izt-detail-section">
          {mode === 'quiz' ? (
            <QuizPanel
              quiz={quiz}
              poles={systemInfo?.poles}
              onCheckQuiz={onButtonClick}
              onNewQuiz={onButtonClick}
              isUpdating={isUpdating}
            />
          ) : (
            <StepDetailPanel
              steps={steps}
              currentStep={currentStep}
              activeMethod={activeMethod}
              methodBSteps={metadata?.method_b_steps}
              methodCTerms={metadata?.method_c_terms}
            />
          )}
        </div>
      </div>

      {/* Impulse Response (shown from step 3+) */}
      {findPlot('impulse_response') && (
        <div className="izt-impulse-section">
          <StemPlot plotData={findPlot('impulse_response')} theme={theme} height={240} />
        </div>
      )}

      {/* Magnitude Response (shown at step 4) */}
      {findPlot('magnitude_response') && (
        <div className="izt-mag-section">
          <StemPlot plotData={findPlot('magnitude_response')} theme={theme} height={200} />
        </div>
      )}

      <style>{`
        .izt-viewer {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          width: 100%;
        }

        /* ── Info Badge ── */
        .izt-info-badge {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          padding: 0.6rem 0.85rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
        }
        .izt-badge-row {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-wrap: wrap;
        }
        .izt-badge-label {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted, #64748b);
          font-weight: 600;
        }
        .izt-badge-value {
          font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
          font-size: 0.82rem;
          color: var(--text-primary, #f1f5f9);
        }
        .izt-badge-pill {
          font-size: 0.68rem;
          padding: 0.15rem 0.55rem;
          border-radius: var(--radius-full, 9999px);
          font-weight: 600;
          letter-spacing: 0.03em;
        }

        /* ── Method Tabs ── */
        .izt-method-tabs {
          display: flex;
          gap: 0.25rem;
          padding: 0.25rem;
          background: var(--surface-color, #131b2e);
          border-radius: var(--radius-lg, 12px);
          border: 1px solid var(--border-color, #1e293b);
        }
        .izt-method-tab {
          flex: 1;
          padding: 0.45rem 0.75rem;
          border: none;
          border-radius: var(--radius-md, 8px);
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          background: transparent;
          color: var(--text-secondary, #94a3b8);
          transition: all var(--transition-fast, 150ms);
        }
        .izt-method-tab:hover {
          color: var(--text-primary, #f1f5f9);
          background: rgba(148, 163, 184, 0.08);
        }
        .izt-method-tab.active {
          background: var(--primary-color, #14b8a6);
          color: white;
        }

        /* ── Stepper ── */
        .izt-stepper {
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
          padding: 0.75rem 1rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
        }
        .izt-step-dots {
          display: flex;
          gap: 0.4rem;
          align-items: center;
        }
        .izt-step-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--border-color, #1e293b);
          transition: background var(--transition-fast, 150ms), transform var(--transition-fast, 150ms);
        }
        .izt-step-dot.active {
          background: var(--primary-color, #14b8a6);
        }
        .izt-step-dot.current {
          transform: scale(1.3);
          box-shadow: 0 0 8px rgba(20, 184, 166, 0.5);
        }
        .izt-step-title {
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
        }
        .izt-step-equation {
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
        .izt-step-description {
          font-size: 0.75rem;
          color: var(--text-secondary, #94a3b8);
          line-height: 1.4;
        }
        .izt-step-actions {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        /* ── Buttons ── */
        .izt-btn {
          padding: 0.4rem 0.9rem;
          border-radius: var(--radius-md, 8px);
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          border: 1px solid transparent;
          transition: all var(--transition-fast, 150ms);
        }
        .izt-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .izt-btn-primary {
          background: var(--primary-color, #14b8a6);
          color: white;
          border-color: var(--primary-color, #14b8a6);
        }
        .izt-btn-primary:hover:not(:disabled) {
          background: var(--primary-hover, #0d9488);
        }
        .izt-btn-secondary {
          background: transparent;
          color: var(--text-secondary, #94a3b8);
          border-color: var(--border-color, #1e293b);
        }
        .izt-btn-secondary:hover:not(:disabled) {
          border-color: var(--border-hover, #334155);
          color: var(--text-primary, #f1f5f9);
        }

        /* ── Main Grid ── */
        .izt-main-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.75rem;
        }
        .izt-pz-section, .izt-detail-section {
          min-width: 0;
        }

        /* ── Detail Panel ── */
        .izt-detail-panel {
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          overflow: hidden;
        }
        .izt-detail-header {
          padding: 0.55rem 0.85rem;
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
          border-bottom: 1px solid var(--border-color, #1e293b);
        }
        .izt-detail-steps {
          max-height: 380px;
          overflow-y: auto;
          padding: 0.5rem;
        }
        .izt-detail-step {
          display: flex;
          gap: 0.5rem;
          padding: 0.5rem;
          border-radius: var(--radius-md, 8px);
          margin-bottom: 0.35rem;
          transition: background var(--transition-fast, 150ms);
        }
        .izt-detail-step--current {
          background: rgba(0, 217, 255, 0.06);
          border-left: 3px solid var(--accent-color, #00d9ff);
        }
        .izt-detail-step-num {
          flex-shrink: 0;
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: var(--primary-color, #14b8a6);
          color: white;
          font-size: 0.7rem;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .izt-detail-step-body {
          flex: 1;
          min-width: 0;
        }
        .izt-detail-step-title {
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
          margin-bottom: 0.15rem;
        }
        .izt-detail-step-eq {
          font-family: 'Fira Code', monospace;
          font-size: 0.75rem;
          color: var(--accent-color, #00d9ff);
          overflow-x: auto;
          white-space: nowrap;
          padding: 0.2rem 0;
        }
        .izt-detail-step-desc {
          font-size: 0.7rem;
          color: var(--text-secondary, #94a3b8);
          margin-top: 0.1rem;
        }

        /* ── Algebra Steps ── */
        .izt-algebra-steps {
          margin-top: 0.4rem;
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
        }
        .izt-algebra-line {
          font-family: 'Fira Code', monospace;
          font-size: 0.7rem;
          color: var(--text-secondary, #94a3b8);
          padding: 0.15rem 0.4rem;
          background: rgba(148, 163, 184, 0.05);
          border-radius: var(--radius-sm, 6px);
          overflow-x: auto;
          white-space: nowrap;
        }

        /* ── Pair Table ── */
        .izt-pairs-table {
          margin-top: 0.4rem;
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }
        .izt-pair-row {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          flex-wrap: wrap;
          padding: 0.3rem 0.5rem;
          border-radius: var(--radius-sm, 6px);
          font-size: 0.7rem;
          font-family: 'Fira Code', monospace;
        }
        .izt-pair-row.causal {
          background: rgba(16, 185, 129, 0.08);
          border-left: 2px solid #10b981;
        }
        .izt-pair-row.anticausal {
          background: rgba(59, 130, 246, 0.08);
          border-left: 2px solid #3b82f6;
        }
        .izt-pair-badge {
          font-size: 0.6rem;
          padding: 0.1rem 0.4rem;
          border-radius: var(--radius-full, 9999px);
          font-weight: 600;
          flex-shrink: 0;
        }
        .causal .izt-pair-badge {
          background: rgba(16, 185, 129, 0.2);
          color: #34d399;
        }
        .anticausal .izt-pair-badge {
          background: rgba(59, 130, 246, 0.2);
          color: #60a5fa;
        }
        .izt-pair-eq {
          color: var(--text-secondary, #94a3b8);
          overflow-x: auto;
          white-space: nowrap;
        }
        .izt-pair-arrow {
          color: var(--text-muted, #64748b);
        }
        .izt-pair-term {
          color: var(--accent-color, #00d9ff);
          font-weight: 500;
        }

        /* ── Method Detail ── */
        .izt-method-detail {
          border-top: 1px solid var(--border-color, #1e293b);
        }
        .izt-long-div-table, .izt-power-series {
          padding: 0.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
          max-height: 200px;
          overflow-y: auto;
        }
        .izt-long-div-row {
          padding: 0.15rem 0.4rem;
        }
        .izt-long-div-eq {
          font-family: 'Fira Code', monospace;
          font-size: 0.75rem;
          color: var(--text-primary, #f1f5f9);
        }
        .izt-ps-term {
          font-family: 'Fira Code', monospace;
          font-size: 0.75rem;
          color: var(--text-primary, #f1f5f9);
          padding: 0.1rem 0.4rem;
        }

        /* ── ROC Selector ── */
        .izt-roc-selector {
          margin-top: 0.5rem;
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          overflow: hidden;
        }
        .izt-roc-header {
          padding: 0.45rem 0.75rem;
          font-size: 0.75rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
          border-bottom: 1px solid var(--border-color, #1e293b);
        }
        .izt-roc-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.5rem;
          padding: 0.4rem 0.75rem;
          border-bottom: 1px solid rgba(30, 41, 59, 0.5);
        }
        .izt-roc-row:last-child {
          border-bottom: none;
        }
        .izt-roc-pole {
          font-family: 'Fira Code', monospace;
          font-size: 0.75rem;
          color: var(--text-primary, #f1f5f9);
        }
        .izt-roc-mag {
          color: var(--text-muted, #64748b);
          font-size: 0.7rem;
          margin-left: 0.3rem;
        }
        .izt-roc-toggle {
          display: flex;
          gap: 0.2rem;
        }
        .izt-roc-btn {
          padding: 0.25rem 0.55rem;
          border-radius: var(--radius-sm, 6px);
          font-size: 0.68rem;
          font-weight: 600;
          cursor: pointer;
          border: 1px solid var(--border-color, #1e293b);
          background: transparent;
          color: var(--text-secondary, #94a3b8);
          transition: all var(--transition-fast, 150ms);
        }
        .izt-roc-btn.active {
          background: rgba(16, 185, 129, 0.15);
          color: #34d399;
          border-color: rgba(16, 185, 129, 0.3);
        }
        .izt-roc-btn.active.anticausal {
          background: rgba(59, 130, 246, 0.15);
          color: #60a5fa;
          border-color: rgba(59, 130, 246, 0.3);
        }

        /* ── Quiz Panel ── */
        .izt-quiz-panel {
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          padding: 0.75rem;
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
        }
        .izt-quiz-header {
          font-size: 0.82rem;
          font-weight: 600;
          color: var(--text-primary, #f1f5f9);
        }
        .izt-quiz-prompt {
          font-size: 0.78rem;
          color: var(--text-secondary, #94a3b8);
          text-align: center;
          padding: 1rem;
        }
        .izt-quiz-row {
          padding: 0.5rem;
          border-radius: var(--radius-md, 8px);
          border: 1px solid var(--border-color, #1e293b);
          transition: border-color var(--transition-fast, 150ms);
        }
        .izt-quiz-row.correct {
          border-color: var(--success-color, #10b981);
          background: rgba(16, 185, 129, 0.05);
        }
        .izt-quiz-row.incorrect {
          border-color: var(--error-color, #ef4444);
          background: rgba(239, 68, 68, 0.05);
        }
        .izt-quiz-pole {
          font-family: 'Fira Code', monospace;
          font-size: 0.78rem;
          color: var(--text-primary, #f1f5f9);
          display: block;
          margin-bottom: 0.3rem;
        }
        .izt-quiz-inputs {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }
        .izt-quiz-inputs label {
          font-size: 0.72rem;
          color: var(--text-secondary, #94a3b8);
          display: flex;
          align-items: center;
          gap: 0.3rem;
        }
        .izt-quiz-input {
          width: 80px;
          padding: 0.3rem 0.5rem;
          border-radius: var(--radius-sm, 6px);
          border: 1px solid var(--border-color, #1e293b);
          background: var(--background-secondary, #111827);
          color: var(--text-primary, #f1f5f9);
          font-family: 'Fira Code', monospace;
          font-size: 0.78rem;
        }
        .izt-quiz-input:focus {
          outline: none;
          border-color: var(--primary-color, #14b8a6);
        }
        .izt-quiz-input:disabled {
          opacity: 0.5;
        }
        .izt-quiz-feedback {
          font-size: 0.72rem;
          font-weight: 600;
          margin-top: 0.25rem;
        }
        .correct .izt-quiz-feedback {
          color: var(--success-color, #10b981);
        }
        .incorrect .izt-quiz-feedback {
          color: var(--error-color, #ef4444);
        }
        .izt-quiz-actions {
          display: flex;
          justify-content: center;
        }

        /* ── Stem Plot ── */
        .izt-stem-plot {
          width: 100%;
          border-radius: var(--radius-lg, 12px);
          overflow: hidden;
        }
        .izt-stem-plot .js-plotly-plot {
          border-radius: var(--radius-md, 8px);
        }

        .izt-impulse-section, .izt-mag-section {
          border-radius: var(--radius-lg, 12px);
          background: var(--surface-color, #131b2e);
          border: 1px solid var(--border-color, #1e293b);
          padding: 0.5rem;
        }

        /* ── Responsive ── */
        @media (max-width: 768px) {
          .izt-main-grid {
            grid-template-columns: 1fr;
          }
          .izt-step-actions {
            flex-wrap: wrap;
          }
          .izt-method-tabs {
            flex-wrap: wrap;
          }
        }
      `}</style>
    </div>
  );
}
