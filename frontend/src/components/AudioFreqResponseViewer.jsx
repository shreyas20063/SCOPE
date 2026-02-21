/**
 * AudioFreqResponseViewer - Interactive Audio Frequency Response Playground
 *
 * Custom viewer for the audio_freq_response simulation.
 * Features:
 * - SVG-based s-plane with click-to-place poles/zeros
 * - Transfer function banner with stability badges
 * - Plotly magnitude, phase, time domain, and spectrum plots
 * - Preset filter buttons and challenge mode
 */

import React, { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/AudioFreqResponseViewer.css';

// ─────────────────────────────────────────────────
// SVG S-Plane Component
// ─────────────────────────────────────────────────

const SVG_W = 600;
const SVG_H = 400;
const PAD = 50;

function SPlaneCanvas({ poles, zeros, placementMode, onAddAtClick, onRemovePole, onRemoveZero, challenge }) {
  const svgRef = useRef(null);

  // Compute axis range from current poles/zeros
  const range = useMemo(() => {
    const allPZ = [...(poles || []), ...(zeros || [])];
    const targetPoles = challenge?.answered ? (challenge.target_poles || []) : [];
    const targetZeros = challenge?.answered ? (challenge.target_zeros || []) : [];
    const allPoints = [...allPZ, ...targetPoles, ...targetZeros];
    if (allPoints.length === 0) return 5000;
    const maxVal = Math.max(...allPoints.map(p => Math.max(Math.abs(p.real), Math.abs(p.imag))));
    return Math.max(maxVal * 1.5, 1000);
  }, [poles, zeros, challenge]);

  // Coordinate transforms
  const toSvgX = useCallback((sigma) => PAD + ((sigma + range) / (2 * range)) * (SVG_W - 2 * PAD), [range]);
  const toSvgY = useCallback((omega) => PAD + ((range - omega) / (2 * range)) * (SVG_H - 2 * PAD), [range]);
  const toSigma = useCallback((svgX) => ((svgX - PAD) / (SVG_W - 2 * PAD)) * (2 * range) - range, [range]);
  const toOmega = useCallback((svgY) => range - ((svgY - PAD) / (SVG_H - 2 * PAD)) * (2 * range), [range]);

  const handleClick = useCallback((e) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const svgX = ((e.clientX - rect.left) / rect.width) * SVG_W;
    const svgY = ((e.clientY - rect.top) / rect.height) * SVG_H;

    // Check bounds
    if (svgX < PAD || svgX > SVG_W - PAD || svgY < PAD || svgY > SVG_H - PAD) return;

    const sigma = toSigma(svgX);
    const omega = toOmega(svgY);

    // Snap small values to zero
    const snapSigma = Math.abs(sigma) < range * 0.02 ? 0 : Math.round(sigma);
    const snapOmega = Math.abs(omega) < range * 0.02 ? 0 : Math.round(omega);

    onAddAtClick(snapSigma, snapOmega);
  }, [toSigma, toOmega, range, onAddAtClick]);

  const handleRemovePole = useCallback((e, index) => {
    e.stopPropagation();
    onRemovePole(index);
  }, [onRemovePole]);

  const handleRemoveZero = useCallback((e, index) => {
    e.stopPropagation();
    onRemoveZero(index);
  }, [onRemoveZero]);

  // Grid lines
  const gridLines = useMemo(() => {
    const lines = [];
    const step = range > 3000 ? 2000 : range > 1000 ? 1000 : 500;
    for (let v = -Math.floor(range / step) * step; v <= range; v += step) {
      if (v === 0) continue;
      // Vertical
      lines.push(
        <line key={`gv${v}`} className="grid-line"
          x1={toSvgX(v)} y1={PAD} x2={toSvgX(v)} y2={SVG_H - PAD} />
      );
      // Horizontal
      lines.push(
        <line key={`gh${v}`} className="grid-line"
          x1={PAD} y1={toSvgY(v)} x2={SVG_W - PAD} y2={toSvgY(v)} />
      );
    }
    return lines;
  }, [range, toSvgX, toSvgY]);

  // Axis tick labels
  const tickLabels = useMemo(() => {
    const labels = [];
    const step = range > 3000 ? 2000 : range > 1000 ? 1000 : 500;
    for (let v = -Math.floor(range / step) * step; v <= range; v += step) {
      if (v === 0) continue;
      // X-axis labels
      if (toSvgX(v) > PAD + 10 && toSvgX(v) < SVG_W - PAD - 10) {
        labels.push(
          <text key={`lx${v}`} className="axis-label" x={toSvgX(v)} y={SVG_H - PAD + 16} textAnchor="middle">
            {v >= 1000 || v <= -1000 ? `${v/1000}k` : v}
          </text>
        );
      }
      // Y-axis labels
      if (toSvgY(v) > PAD + 10 && toSvgY(v) < SVG_H - PAD - 10) {
        labels.push(
          <text key={`ly${v}`} className="axis-label" x={PAD - 8} y={toSvgY(v) + 4} textAnchor="end">
            {v >= 1000 || v <= -1000 ? `${v/1000}k` : v}
          </text>
        );
      }
    }
    return labels;
  }, [range, toSvgX, toSvgY]);

  // Find conjugate pairs for connecting lines
  const conjugateLines = useMemo(() => {
    const lines = [];
    const seen = new Set();
    (poles || []).forEach((p, i) => {
      if (seen.has(i) || Math.abs(p.imag) < 1) return;
      // Find conjugate
      (poles || []).forEach((p2, j) => {
        if (j <= i || seen.has(j)) return;
        if (Math.abs(p.real - p2.real) < 1 && Math.abs(p.imag + p2.imag) < 1) {
          seen.add(i);
          seen.add(j);
          lines.push(
            <line key={`cp${i}-${j}`} className="conjugate-line"
              x1={toSvgX(p.real)} y1={toSvgY(p.imag)}
              x2={toSvgX(p2.real)} y2={toSvgY(p2.imag)} />
          );
        }
      });
    });
    (zeros || []).forEach((z, i) => {
      if (seen.has(`z${i}`) || Math.abs(z.imag) < 1) return;
      (zeros || []).forEach((z2, j) => {
        if (j <= i || seen.has(`z${j}`)) return;
        if (Math.abs(z.real - z2.real) < 1 && Math.abs(z.imag + z2.imag) < 1) {
          seen.add(`z${i}`);
          seen.add(`z${j}`);
          lines.push(
            <line key={`cz${i}-${j}`} className="conjugate-line"
              x1={toSvgX(z.real)} y1={toSvgY(z.imag)}
              x2={toSvgX(z2.real)} y2={toSvgY(z2.imag)} />
          );
        }
      });
    });
    return lines;
  }, [poles, zeros, toSvgX, toSvgY]);

  const markerSize = 8;

  return (
    <div className="afr-splane-container">
      <svg
        ref={svgRef}
        className="afr-splane-svg"
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        onClick={handleClick}
        aria-label={`S-plane. Click to add ${placementMode}. Currently ${(poles || []).length} poles and ${(zeros || []).length} zeros.`}
        role="img"
      >
        {/* Stable region fill */}
        <rect className="stable-region"
          x={PAD} y={PAD}
          width={toSvgX(0) - PAD} height={SVG_H - 2 * PAD} />

        {/* Grid */}
        {gridLines}

        {/* Real axis */}
        <line className="axis-line"
          x1={PAD} y1={toSvgY(0)} x2={SVG_W - PAD} y2={toSvgY(0)} />

        {/* jw axis (imaginary) */}
        <line className="jw-axis"
          x1={toSvgX(0)} y1={PAD} x2={toSvgX(0)} y2={SVG_H - PAD} />

        {/* Axis labels */}
        <text className="axis-label" x={SVG_W - PAD + 5} y={toSvgY(0) + 4} textAnchor="start">σ</text>
        <text className="axis-label" x={toSvgX(0) + 6} y={PAD - 5} textAnchor="start">jω</text>
        {tickLabels}

        {/* Conjugate pair lines */}
        {conjugateLines}

        {/* Challenge target poles/zeros (after answer) */}
        {challenge?.answered && challenge.target_poles && challenge.target_poles.map((p, i) => (
          <g key={`tp${i}`}>
            <line className="target-pole"
              x1={toSvgX(p.real) - markerSize} y1={toSvgY(p.imag) - markerSize}
              x2={toSvgX(p.real) + markerSize} y2={toSvgY(p.imag) + markerSize} />
            <line className="target-pole"
              x1={toSvgX(p.real) + markerSize} y1={toSvgY(p.imag) - markerSize}
              x2={toSvgX(p.real) - markerSize} y2={toSvgY(p.imag) + markerSize} />
          </g>
        ))}
        {challenge?.answered && challenge.target_zeros && challenge.target_zeros.map((z, i) => (
          <circle key={`tz${i}`} className="target-zero"
            cx={toSvgX(z.real)} cy={toSvgY(z.imag)} r={markerSize} />
        ))}

        {/* Zeros (circles) */}
        {(zeros || []).map((z, i) => (
          <circle key={`z${i}`} className="zero-marker"
            cx={toSvgX(z.real)} cy={toSvgY(z.imag)} r={markerSize}
            onClick={(e) => handleRemoveZero(e, z.index ?? i)}
            aria-label={`Zero at σ=${z.real.toFixed(0)}, ω=${z.imag.toFixed(0)}. Click to remove.`}
          >
            <title>Zero {i + 1}: σ={z.real.toFixed(0)}, ω={z.imag.toFixed(0)} — Click to remove</title>
          </circle>
        ))}

        {/* Poles (X markers) */}
        {(poles || []).map((p, i) => (
          <g key={`p${i}`}
            onClick={(e) => handleRemovePole(e, p.index ?? i)}
            style={{ cursor: 'pointer' }}
            aria-label={`Pole at σ=${p.real.toFixed(0)}, ω=${p.imag.toFixed(0)}. Click to remove.`}
          >
            <title>Pole {i + 1}: σ={p.real.toFixed(0)}, ω={p.imag.toFixed(0)} — Click to remove</title>
            <line className="pole-marker"
              x1={toSvgX(p.real) - markerSize} y1={toSvgY(p.imag) - markerSize}
              x2={toSvgX(p.real) + markerSize} y2={toSvgY(p.imag) + markerSize} />
            <line className="pole-marker"
              x1={toSvgX(p.real) + markerSize} y1={toSvgY(p.imag) - markerSize}
              x2={toSvgX(p.real) - markerSize} y2={toSvgY(p.imag) + markerSize} />
          </g>
        ))}

        {/* Placement mode indicator */}
        <text x={PAD + 6} y={PAD + 14} fill="var(--text-muted)" fontSize="10" fontFamily="Inter, sans-serif">
          Click to add {placementMode === 'pole' ? '× Pole' : '○ Zero'}
        </text>
      </svg>
    </div>
  );
}

// ─────────────────────────────────────────────────
// Challenge Panel
// ─────────────────────────────────────────────────

function ChallengePanel({ challenge, onNewChallenge, onCheckAnswer, isUpdating }) {
  const [difficulty, setDifficulty] = useState(challenge?.difficulty || 'easy');

  const handleNewChallenge = useCallback(() => {
    onNewChallenge(difficulty);
  }, [onNewChallenge, difficulty]);

  if (!challenge) return null;

  const scoreClass = challenge.score >= 80 ? 'excellent' : challenge.score >= 50 ? 'good' : 'poor';

  return (
    <div className="afr-challenge-panel" role="region" aria-label="Challenge mode">
      {challenge.active && !challenge.answered && (
        <>
          <span className="afr-challenge-panel__prompt">
            Match the amber target curve by placing poles and zeros on the s-plane!
          </span>
          {challenge.hint && (
            <span className="afr-challenge-panel__hint">
              Hint: {challenge.hint}
            </span>
          )}
          <button className="afr-challenge-panel__btn" onClick={onCheckAnswer} disabled={isUpdating}
            aria-label="Check your answer">
            Check Answer
          </button>
        </>
      )}
      {challenge.active && challenge.answered && (
        <>
          <span className={`afr-challenge-panel__score afr-challenge-panel__score--${scoreClass}`}>
            Score: {challenge.score}/100
          </span>
          {challenge.filter_name && (
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Target: {challenge.filter_name}
            </span>
          )}
          <div className="afr-challenge-panel__difficulty">
            {['easy', 'medium', 'hard'].map(d => (
              <button key={d}
                className={`afr-challenge-panel__diff-btn ${d === difficulty ? 'afr-challenge-panel__diff-btn--active' : ''}`}
                onClick={() => setDifficulty(d)}
              >
                {d}
              </button>
            ))}
          </div>
          <button className="afr-challenge-panel__btn" onClick={handleNewChallenge} disabled={isUpdating}>
            Next Challenge
          </button>
        </>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────
// Main Viewer Component
// ─────────────────────────────────────────────────

function AudioFreqResponseViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const poles = metadata?.poles || [];
  const zeros = metadata?.zeros || [];
  const placementMode = metadata?.placement_mode || 'pole';
  const isStable = metadata?.is_stable !== false;
  const hasMarginal = metadata?.has_marginal_poles === true;
  const tfExpression = metadata?.tf_expression || 'H(s) = 1';
  const filterType = metadata?.filter_type || 'flat';
  const challenge = metadata?.challenge || null;
  const presets = metadata?.presets || ['lowpass', 'highpass', 'bandpass', 'notch', 'resonant', 'allpass'];
  const errorMsg = metadata?.error;

  // Track system fingerprint for resetting local state
  const systemFP = useMemo(() =>
    `${poles.length}-${zeros.length}-${JSON.stringify(poles)}-${JSON.stringify(zeros)}`,
    [poles, zeros]
  );
  const prevFP = useRef(systemFP);
  useEffect(() => {
    prevFP.current = systemFP;
  }, [systemFP]);

  // ── Action handlers ──

  const handleAddAtClick = useCallback((real, imag) => {
    if (isUpdating) return;
    onButtonClick('add_at_click', { real, imag });
  }, [onButtonClick, isUpdating]);

  const handleRemovePole = useCallback((index) => {
    if (isUpdating) return;
    onButtonClick('remove_pole', { index });
  }, [onButtonClick, isUpdating]);

  const handleRemoveZero = useCallback((index) => {
    if (isUpdating) return;
    onButtonClick('remove_zero', { index });
  }, [onButtonClick, isUpdating]);

  const handleSetMode = useCallback((mode) => {
    onButtonClick('set_placement_mode', { mode });
  }, [onButtonClick]);

  const handleClearAll = useCallback(() => {
    if (isUpdating) return;
    onButtonClick('clear_all', {});
  }, [onButtonClick, isUpdating]);

  const handleLoadPreset = useCallback((preset) => {
    if (isUpdating) return;
    onButtonClick('load_preset', { preset });
  }, [onButtonClick, isUpdating]);

  const handleNewChallenge = useCallback((difficulty) => {
    if (isUpdating) return;
    onButtonClick('new_challenge', { difficulty });
  }, [onButtonClick, isUpdating]);

  const handleCheckAnswer = useCallback(() => {
    if (isUpdating) return;
    onButtonClick('check_answer', {});
  }, [onButtonClick, isUpdating]);

  // ── Split plots ──

  const sPlane = useMemo(() => plots?.find(p => p.id === 's_plane'), [plots]);
  const magPlot = useMemo(() => plots?.find(p => p.id === 'magnitude_response'), [plots]);
  const phasePlot = useMemo(() => plots?.find(p => p.id === 'phase_response'), [plots]);
  const timePlot = useMemo(() => plots?.find(p => p.id === 'time_domain'), [plots]);
  const spectrumPlot = useMemo(() => plots?.find(p => p.id === 'spectrum'), [plots]);

  // ── Stability badge ──

  const stabilityBadge = useMemo(() => {
    if (poles.length === 0) return null;
    if (!isStable) return <span className="afr-badge afr-badge--unstable">Unstable</span>;
    if (hasMarginal) return <span className="afr-badge afr-badge--marginal">Marginally Stable</span>;
    return <span className="afr-badge afr-badge--stable">Stable</span>;
  }, [poles.length, isStable, hasMarginal]);

  // ── Filter type badge ──

  const filterBadge = useMemo(() => {
    if (filterType === 'flat' || filterType === 'custom') return null;
    return <span className="afr-badge afr-badge--filter">{filterType}</span>;
  }, [filterType]);

  return (
    <div className="afr-viewer">
      {/* Transfer function banner */}
      <div className="afr-tf-banner">
        <span className="afr-tf-expression">{tfExpression}</span>
        {stabilityBadge}
        {filterBadge}
      </div>

      {/* Info cards */}
      <div className="afr-info-row">
        <div className="afr-info-card">
          <span className="afr-info-card__label">Order</span>
          <span className="afr-info-card__value">{metadata?.system_order ?? 0}</span>
        </div>
        <div className="afr-info-card">
          <span className="afr-info-card__label">Poles</span>
          <span className="afr-info-card__value" style={{ color: '#ef4444' }}>{poles.length}</span>
        </div>
        <div className="afr-info-card">
          <span className="afr-info-card__label">Zeros</span>
          <span className="afr-info-card__value" style={{ color: '#3b82f6' }}>{zeros.length}</span>
        </div>
        <div className="afr-info-card">
          <span className="afr-info-card__label">Gain K</span>
          <span className="afr-info-card__value">{metadata?.gain_K ?? 1}</span>
        </div>
      </div>

      {/* Error message */}
      {errorMsg && (
        <div className="afr-error" role="alert">{errorMsg}</div>
      )}

      {/* Challenge panel */}
      {challenge && (
        <ChallengePanel
          challenge={challenge}
          onNewChallenge={handleNewChallenge}
          onCheckAnswer={handleCheckAnswer}
          isUpdating={isUpdating}
        />
      )}

      {/* Interactive S-Plane (SVG) */}
      <SPlaneCanvas
        poles={poles}
        zeros={zeros}
        placementMode={placementMode}
        onAddAtClick={handleAddAtClick}
        onRemovePole={handleRemovePole}
        onRemoveZero={handleRemoveZero}
        challenge={challenge}
      />

      {/* Placement toolbar */}
      <div className="afr-toolbar" role="toolbar" aria-label="S-plane tools">
        <div className="afr-toolbar__group">
          <button
            className={`afr-toolbar__btn ${placementMode === 'pole' ? 'afr-toolbar__btn--active-pole' : ''}`}
            onClick={() => handleSetMode('pole')}
            aria-pressed={placementMode === 'pole'}
          >
            × Add Pole
          </button>
          <button
            className={`afr-toolbar__btn ${placementMode === 'zero' ? 'afr-toolbar__btn--active-zero' : ''}`}
            onClick={() => handleSetMode('zero')}
            aria-pressed={placementMode === 'zero'}
          >
            ○ Add Zero
          </button>
          <button
            className="afr-toolbar__btn afr-toolbar__btn--danger"
            onClick={handleClearAll}
            disabled={isUpdating || (poles.length === 0 && zeros.length === 0)}
            aria-label="Clear all poles and zeros"
          >
            Clear All
          </button>
        </div>

        <div className="afr-toolbar__separator" />

        {/* Preset buttons */}
        <div className="afr-toolbar__group">
          {presets.map(preset => (
            <button key={preset}
              className="afr-toolbar__btn afr-toolbar__btn--preset"
              onClick={() => handleLoadPreset(preset)}
              disabled={isUpdating}
            >
              {preset.charAt(0).toUpperCase() + preset.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Magnitude + Phase plots */}
      <div className="afr-plots-grid">
        {magPlot && <PlotDisplay plots={[magPlot]} />}
        {phasePlot && <PlotDisplay plots={[phasePlot]} />}
      </div>

      {/* Time domain + Spectrum plots */}
      <div className="afr-plots-grid">
        {timePlot && <PlotDisplay plots={[timePlot]} />}
        {spectrumPlot && <PlotDisplay plots={[spectrumPlot]} />}
      </div>
    </div>
  );
}

export default AudioFreqResponseViewer;
