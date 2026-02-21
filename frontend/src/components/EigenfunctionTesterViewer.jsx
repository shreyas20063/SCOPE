/**
 * EigenfunctionTesterViewer
 *
 * Custom viewer for the Eigenfunction Tester Lab simulation.
 * Shows signal palette, eigenfunction verdict, eigenvalue card,
 * s-plane with vectors, and quiz mode.
 */

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/EigenfunctionTesterViewer.css';

// ── Theme hook ──────────────────────────────────────────────────────

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

// ── Complex number formatter ────────────────────────────────────────

function formatComplex(real, imag, precision = 4) {
  if (imag === undefined || imag === null) return `${real.toFixed(precision)}`;
  if (Math.abs(imag) < 1e-6) return `${real.toFixed(precision)}`;
  if (Math.abs(real) < 1e-6) {
    if (Math.abs(imag - 1.0) < 1e-6) return 'j';
    if (Math.abs(imag + 1.0) < 1e-6) return '\u2212j';
    return `${imag.toFixed(precision)}j`;
  }
  const sign = imag >= 0 ? '+' : '\u2212';
  return `${real.toFixed(precision)} ${sign} ${Math.abs(imag).toFixed(precision)}j`;
}

function formatPole(pole) {
  if (!pole) return '\u2014';
  return formatComplex(pole.real, pole.imag, 3);
}

// ── System Banner ───────────────────────────────────────────────────

function SystemBanner({ metadata }) {
  if (!metadata) return null;

  const poles = metadata.poles || [];
  const zeros = metadata.zeros || [];

  return (
    <div className="ef-system-banner">
      <span className="ef-system-label">H(s) =</span>
      <span className="ef-hs-expression">{metadata.hs_expression || '...'}</span>
      <div className="ef-pole-zero-summary">
        {poles.length > 0 && (
          <span className="ef-pz-badge poles">
            {'\u00d7'} {poles.length} pole{poles.length > 1 ? 's' : ''}
            <span style={{ marginLeft: 4 }}>
              {poles.map((p, i) => (
                <span key={i}>{i > 0 ? ', ' : ''}{formatPole(p)}</span>
              ))}
            </span>
          </span>
        )}
        {zeros.length > 0 && (
          <span className="ef-pz-badge zeros">
            {'\u25cb'} {zeros.length} zero{zeros.length > 1 ? 's' : ''}
            <span style={{ marginLeft: 4 }}>
              {zeros.map((z, i) => (
                <span key={i}>{i > 0 ? ', ' : ''}{formatPole(z)}</span>
              ))}
            </span>
          </span>
        )}
      </div>
    </div>
  );
}

// ── Signal Palette ──────────────────────────────────────────────────

function SignalPalette({ signals, activeSignal, onSelect }) {
  if (!signals || signals.length === 0) return null;

  return (
    <div className="ef-signal-palette" role="radiogroup" aria-label="Test signal selection">
      {signals.map(sig => {
        const isActive = activeSignal === sig.key;
        const sLabel = sig.s_value && sig.s_value !== 'from_params'
          ? `s = ${formatComplex(sig.s_value.real, sig.s_value.imag, 0)}`
          : sig.key === 'custom_exp' ? 's = custom' : null;

        return (
          <button
            key={sig.key}
            className={`ef-signal-card ${sig.category} ${isActive ? 'active' : ''}`}
            onClick={() => onSelect(sig.key)}
            role="radio"
            aria-checked={isActive}
            aria-label={`Test signal ${sig.latex || sig.label}`}
          >
            <span className="ef-signal-expr">{sig.label}</span>
            {sLabel && <span className="ef-signal-s-value">{sLabel}</span>}
            <span className="ef-signal-category-tag">{sig.category}</span>
          </button>
        );
      })}
    </div>
  );
}

// ── Verdict Banner ──────────────────────────────────────────────────

function VerdictBanner({ metadata }) {
  if (!metadata) return null;

  const isEigen = metadata.is_eigenfunction;
  const atPole = metadata.at_pole;
  const label = metadata.test_signal_label || '';

  if (atPole) {
    return (
      <div className="ef-verdict at-pole">
        <div className="ef-verdict-icon">{'\u26a0'}</div>
        <div className="ef-verdict-content">
          <div className="ef-verdict-title">
            <strong>{label}</strong> hits a pole of H(s)
          </div>
          <div className="ef-verdict-reason">
            The evaluation point s is a pole of the system, so H(s) = {'\u221e'}. The eigenvalue is undefined at this point.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`ef-verdict ${isEigen ? 'is-eigen' : 'not-eigen'}`}>
      <div className="ef-verdict-icon">
        {isEigen ? '\u2713' : '\u2717'}
      </div>
      <div className="ef-verdict-content">
        <div className="ef-verdict-title">
          <strong>{label}</strong>
          {isEigen
            ? ' IS an eigenfunction of this system'
            : ' is NOT an eigenfunction of this system'}
        </div>
        <div className="ef-verdict-reason">
          {isEigen
            ? 'Output is a scalar multiple of input: y(t) = H(s) \u00b7 x(t). The eigenvalue \u03bb = H(s).'
            : 'Output shape differs from input \u2014 the ratio y(t)/x(t) is NOT constant. Only complex exponentials e^{st} are eigenfunctions of LTI systems.'}
        </div>
      </div>
    </div>
  );
}

// ── Eigenvalue Card ─────────────────────────────────────────────────

function EigenvalueCard({ metadata }) {
  if (!metadata?.is_eigenfunction || !metadata?.eigenvalue) return null;

  const ev = metadata.eigenvalue;
  const s = metadata.s_value;

  return (
    <div className="ef-eigenvalue-card">
      <div className="ef-eigenvalue-header">
        Eigenvalue {'\u03bb'} = H(s)
      </div>
      <div className="ef-eigenvalue-grid">
        <div className="ef-ev-item">
          <span className="ef-ev-label">H(s) rectangular</span>
          <span className="ef-ev-value">{formatComplex(ev.real, ev.imag)}</span>
        </div>
        <div className="ef-ev-item">
          <span className="ef-ev-label">|H(s)| magnitude</span>
          <span className="ef-ev-value">{ev.magnitude.toFixed(4)}</span>
        </div>
        <div className="ef-ev-item">
          <span className="ef-ev-label">{'\u2220'}H(s) angle</span>
          <span className="ef-ev-value">{ev.angle_deg.toFixed(1)}{'\u00b0'}</span>
        </div>
        {s && (
          <div className="ef-ev-item">
            <span className="ef-ev-label">at s =</span>
            <span className="ef-ev-value">{formatComplex(s.real, s.imag, 3)}</span>
          </div>
        )}
      </div>
      <div className="ef-ev-equation">
        y(t) = H(s) {'\u00b7'} e^(st) = {formatComplex(ev.real, ev.imag)} {'\u00b7'} e^({s ? formatComplex(s.real, s.imag, 1) : 's'}{'\u00b7'}t)
      </div>
    </div>
  );
}

// ── Quiz Panel ──────────────────────────────────────────────────────

function QuizPanel({ quiz, onAnswer, onNewQuiz, isUpdating }) {
  if (!quiz) return null;

  return (
    <div className="ef-quiz-panel" role="region" aria-label="Quiz mode">
      {!quiz.answered ? (
        <>
          <div className="ef-quiz-question">
            For the system <strong>{quiz.quiz_system_label}</strong>,
            is <strong>{quiz.quiz_signal_label}</strong> an eigenfunction?
          </div>
          <div className="ef-quiz-buttons">
            <button
              className="ef-quiz-btn yes"
              onClick={() => onAnswer('yes')}
              disabled={isUpdating}
              aria-label="Yes, it is an eigenfunction"
            >
              {'\u2713'} Yes, Eigenfunction
            </button>
            <button
              className="ef-quiz-btn no"
              onClick={() => onAnswer('no')}
              disabled={isUpdating}
              aria-label="No, it is not an eigenfunction"
            >
              {'\u2717'} No, Not Eigenfunction
            </button>
          </div>
        </>
      ) : (
        <div className="ef-quiz-result">
          <span className={`ef-quiz-feedback ${quiz.correct ? 'correct' : 'incorrect'}`}>
            {quiz.correct ? 'Correct!' : 'Incorrect.'}
          </span>
          <span className="ef-quiz-explanation">
            {quiz.expected === 'yes'
              ? `${quiz.quiz_signal_label} is a complex exponential e^{st}, which is always an eigenfunction of any LTI system. The eigenvalue is H(s).`
              : `${quiz.quiz_signal_label} is not of the form e^{st}. Only complex exponentials are eigenfunctions of ALL LTI systems. The output shape differs from the input.`}
          </span>
          <button
            className="ef-quiz-next"
            onClick={onNewQuiz}
            disabled={isUpdating}
          >
            Next Question {'\u2192'}
          </button>
        </div>
      )}
    </div>
  );
}

// ── Main Viewer ─────────────────────────────────────────────────────

function EigenfunctionTesterViewer({
  metadata,
  plots,
  currentParams,
  onParamChange,
  onButtonClick,
  isUpdating,
}) {
  const theme = useTheme();
  const isQuizMode = metadata?.mode === 'quiz';

  // Track system fingerprint to reset local state on system change
  const systemFingerprint = useMemo(() => {
    if (!metadata) return '';
    const preset = currentParams?.system_preset || '';
    const signal = currentParams?.test_signal || '';
    const sr = currentParams?.custom_s_real || 0;
    const si = currentParams?.custom_s_imag || 0;
    return `${preset}-${signal}-${sr}-${si}-${metadata.revision || 0}`;
  }, [metadata, currentParams]);

  const prevFingerprintRef = useRef(systemFingerprint);
  useEffect(() => {
    prevFingerprintRef.current = systemFingerprint;
  }, [systemFingerprint]);

  // Split plots by ID
  const timeDomainPlots = useMemo(
    () => (plots || []).filter(p => p.id === 'time_domain'),
    [plots]
  );
  const ratioPlots = useMemo(
    () => (plots || []).filter(p => p.id === 'ratio_plot'),
    [plots]
  );
  const splanePlots = useMemo(
    () => (plots || []).filter(p => p.id === 's_plane'),
    [plots]
  );

  // Handlers
  const handleSignalSelect = useCallback((key) => {
    if (onParamChange) onParamChange('test_signal', key);
  }, [onParamChange]);

  const handleQuizAnswer = useCallback((answer) => {
    if (onButtonClick) onButtonClick('check_answer', { answer });
  }, [onButtonClick]);

  const handleNewQuiz = useCallback(() => {
    if (onButtonClick) onButtonClick('new_quiz', {});
  }, [onButtonClick]);

  return (
    <div className="ef-viewer">
      {/* System info banner */}
      <SystemBanner metadata={metadata} />

      {/* Quiz panel (if quiz mode) */}
      {isQuizMode && (
        <QuizPanel
          quiz={metadata?.quiz}
          onAnswer={handleQuizAnswer}
          onNewQuiz={handleNewQuiz}
          isUpdating={isUpdating}
        />
      )}

      {/* Signal palette (explore mode) */}
      {!isQuizMode && (
        <SignalPalette
          signals={metadata?.signal_palette}
          activeSignal={currentParams?.test_signal}
          onSelect={handleSignalSelect}
        />
      )}

      {/* Verdict banner (explore mode, or after quiz answer) */}
      {(!isQuizMode || (isQuizMode && metadata?.quiz?.answered)) && (
        <VerdictBanner metadata={metadata} />
      )}

      {/* Eigenvalue card (only for eigenfunctions in explore mode) */}
      {!isQuizMode && <EigenvalueCard metadata={metadata} />}
      {isQuizMode && metadata?.quiz?.answered && <EigenvalueCard metadata={metadata} />}

      {/* Plots: s-plane + time domain in a row */}
      <div className="ef-plots-row">
        {splanePlots.length > 0 && (
          <div className="ef-plot-splane">
            <PlotDisplay plots={splanePlots} isLoading={false} emptyMessage="No s-plane data" />
          </div>
        )}
        <div className="ef-plot-time">
          <PlotDisplay plots={timeDomainPlots} isLoading={false} emptyMessage="No signal data" />
        </div>
      </div>

      {/* Ratio plot (full width below) */}
      {ratioPlots.length > 0 && (
        <div className="ef-plot-ratio">
          <PlotDisplay plots={ratioPlots} isLoading={false} emptyMessage="No ratio data" />
        </div>
      )}
    </div>
  );
}

export default EigenfunctionTesterViewer;
