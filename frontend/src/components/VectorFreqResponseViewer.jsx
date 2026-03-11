/**
 * VectorFreqResponseViewer
 *
 * Custom viewer for the Vector Diagram Frequency Response Builder.
 * Animates the ω sweep along the jω axis, drawing vectors from poles/zeros
 * to s₀ = jω, and progressively building up the magnitude/phase curves.
 *
 * Overhauled layout:
 * - TF input banner with KaTeX live preview (type any expression)
 * - Full-width s-plane (550px) with proper Plotly annotation arrows
 * - Side-by-side magnitude + phase below
 * - Animation controls + readout
 *
 * Animation runs entirely client-side using requestAnimationFrame.
 * Backend provides pole/zero positions and precomputed frequency response arrays.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import PlotDisplay from './PlotDisplay';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/VectorFreqResponseViewer.css';

const FRAME_INTERVAL_BASE = 40; // ~25fps base

/* ======================================================================
   TF Expression to LaTeX
   ====================================================================== */
function tfExprToLatex(expression) {
  if (!expression) return '';
  const expr = expression.trim();
  // Handle (num)/(den) or num/den
  const ratioMatch = expr.match(/^\(([^)]+)\)\s*\/\s*\(([^)]+)\)$/) ||
                     expr.match(/^([^/]+)\/(.+)$/);
  if (ratioMatch) {
    const num = ratioMatch[1].trim();
    const den = ratioMatch[2].trim();
    return `H(s) = \\frac{${num}}{${den}}`;
  }
  return `H(s) = ${expr}`;
}

/* ======================================================================
   TF Input Banner
   ====================================================================== */
function TransferFunctionBanner({ metadata, onParseExpression }) {
  const [tfInput, setTfInput] = useState('');
  const error = metadata?.error;

  // KaTeX preview
  const latexPreview = useMemo(() => {
    if (tfInput.trim()) {
      const latex = tfExprToLatex(tfInput);
      try {
        return katex.renderToString(latex, { throwOnError: false, displayMode: false });
      } catch {
        return null;
      }
    }
    // Show current TF from metadata
    if (metadata?.num_display && metadata?.den_display) {
      const gain = metadata?.gain;
      const gainPrefix = gain && Math.abs(gain - 1.0) > 1e-6 ? `${gain} \\cdot ` : '';
      const latex = metadata.den_display === '1'
        ? `H(s) = ${gainPrefix}${metadata.num_display}`
        : `H(s) = ${gainPrefix}\\frac{${metadata.num_display}}{${metadata.den_display}}`;
      try {
        return katex.renderToString(latex, { throwOnError: false, displayMode: false });
      } catch {
        return null;
      }
    }
    return null;
  }, [tfInput, metadata?.num_display, metadata?.den_display, metadata?.gain]);

  const handleSubmit = useCallback(() => {
    const expr = tfInput.trim();
    if (!expr) return;
    if (onParseExpression) {
      onParseExpression(expr);
    }
  }, [tfInput, onParseExpression]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <div className="vfr-tf-banner">
      <div className="vfr-tf-input-area">
        <div className="vfr-tf-input-row">
          <label className="vfr-tf-label">H(s)</label>
          <input
            className="vfr-tf-input"
            type="text"
            value={tfInput}
            onChange={(e) => setTfInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleSubmit}
            placeholder="e.g. (s+1)/(s^2+2s+1)"
            spellCheck={false}
          />
          <button className="vfr-tf-apply-btn" onClick={handleSubmit}>Apply</button>
        </div>
        {latexPreview && (
          <div
            className="vfr-tf-preview"
            dangerouslySetInnerHTML={{ __html: latexPreview }}
          />
        )}
        {error && (
          <div className="vfr-error-banner">{error}</div>
        )}
      </div>

      <div className="vfr-tf-badges">
        {metadata?.preset_name && (
          <span className="vfr-preset-badge">{metadata.preset_name}</span>
        )}
        {metadata?.system_order != null && (
          <span className="vfr-order-badge">Order {metadata.system_order}</span>
        )}
        <span className="vfr-pz-badge">
          {(metadata?.poles?.length || 0)}P / {(metadata?.zeros?.length || 0)}Z
        </span>
      </div>
    </div>
  );
}

/* ======================================================================
   Main Viewer
   ====================================================================== */
function VectorFreqResponseViewer({ metadata, plots, currentParams, onParamChange, onButtonClick, isUpdating }) {
  // Animation state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const animFrameRef = useRef(null);
  const lastFrameTimeRef = useRef(0);
  const indexRef = useRef(0);

  // Extract data from metadata
  const omega = metadata?.omega || [];
  const magnitude = metadata?.magnitude || [];
  const phase = metadata?.phase || [];
  const poles = metadata?.poles || [];
  const zeros = metadata?.zeros || [];
  const gain = metadata?.gain || 1;
  const axisRange = metadata?.axis_range || 5;
  const numPoints = omega.length;

  // System fingerprint: reset animation when system changes
  const fingerprint = useMemo(() => {
    const p = JSON.stringify(poles);
    const z = JSON.stringify(zeros);
    return `${metadata?.preset_name}-${p}-${z}-${gain}-${metadata?.hs_expression}`;
  }, [metadata?.preset_name, poles, zeros, gain, metadata?.hs_expression]);

  useEffect(() => {
    setCurrentIndex(0);
    indexRef.current = 0;
    setIsPlaying(false);
  }, [fingerprint]);

  useEffect(() => {
    indexRef.current = currentIndex;
  }, [currentIndex]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || numPoints === 0) return;

    let active = true;
    const interval = Math.max(15, Math.floor(FRAME_INTERVAL_BASE / speed));

    const step = () => {
      if (!active) return;
      const now = performance.now();
      if (now - lastFrameTimeRef.current >= interval) {
        lastFrameTimeRef.current = now;
        const next = indexRef.current + 1;
        if (next >= numPoints) {
          indexRef.current = 0;
          setCurrentIndex(0);
        } else {
          indexRef.current = next;
          setCurrentIndex(next);
        }
      }
      animFrameRef.current = requestAnimationFrame(step);
    };

    animFrameRef.current = requestAnimationFrame(step);

    return () => {
      active = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isPlaying, numPoints, speed]);

  // Transport handlers
  const togglePlay = useCallback(() => setIsPlaying(prev => !prev), []);

  const stepBack = useCallback(() => {
    setIsPlaying(false);
    setCurrentIndex(prev => Math.max(0, prev - 5));
  }, []);

  const stepForward = useCallback(() => {
    setIsPlaying(false);
    setCurrentIndex(prev => Math.min(numPoints - 1, prev + 5));
  }, [numPoints]);

  const handleSliderChange = useCallback((e) => {
    const idx = parseInt(e.target.value, 10);
    setCurrentIndex(idx);
    indexRef.current = idx;
  }, []);

  const handleSpeedChange = useCallback((e) => {
    setSpeed(parseFloat(e.target.value));
  }, []);

  const handleParseExpression = useCallback((expr) => {
    if (onButtonClick) {
      onButtonClick('parse_expression', { expression: expr });
    }
  }, [onButtonClick]);

  // Current values
  const currentOmega = numPoints > 0 ? omega[currentIndex] || 0 : 0;
  const currentMag = numPoints > 0 ? magnitude[currentIndex] || 0 : 0;
  const currentPhase = numPoints > 0 ? phase[currentIndex] || 0 : 0;

  // Build s-plane plot with annotation-based vector arrows
  const sPlaneWithVectors = useMemo(() => {
    const basePlot = plots?.find(p => p.id === 's_plane');
    if (!basePlot || numPoints === 0) return basePlot;

    const w = currentOmega;
    const traces = [...(basePlot.data || [])];
    const annotations = [];

    // Draw annotation arrows from each zero to jω₀
    zeros.forEach((z, i) => {
      annotations.push({
        x: 0, y: w,
        ax: z.real, ay: z.imag,
        xref: 'x', yref: 'y', axref: 'x', ayref: 'y',
        showarrow: true,
        arrowhead: 2,
        arrowsize: 1.5,
        arrowwidth: 2.5,
        arrowcolor: '#3b82f6',
        opacity: 0.9,
      });
    });

    // Draw annotation arrows from each pole to jω₀
    poles.forEach((p, i) => {
      annotations.push({
        x: 0, y: w,
        ax: p.real, ay: p.imag,
        xref: 'x', yref: 'y', axref: 'x', ayref: 'y',
        showarrow: true,
        arrowhead: 2,
        arrowsize: 1.5,
        arrowwidth: 2.5,
        arrowcolor: '#ef4444',
        opacity: 0.9,
      });
    });

    // Current evaluation point s₀ = jω₀
    traces.push({
      x: [0],
      y: [w],
      type: 'scatter',
      mode: 'markers',
      marker: {
        symbol: 'circle',
        size: 12,
        color: '#10b981',
        line: { width: 2, color: '#10b981' },
      },
      name: `s₀ = j${w.toFixed(2)}`,
      showlegend: true,
      hovertemplate: `s₀ = j${w.toFixed(2)}<br>|H| = ${currentMag.toFixed(3)}<br>∠H = ${currentPhase.toFixed(3)} rad<extra></extra>`,
    });

    return {
      ...basePlot,
      data: traces,
      layout: {
        ...basePlot.layout,
        annotations: annotations,
        datarevision: `splane-${currentIndex}-${Date.now()}`,
      },
    };
  }, [plots, currentIndex, currentOmega, currentMag, currentPhase, poles, zeros, numPoints]);

  // Build magnitude plot with progressive reveal
  const magPlotAnimated = useMemo(() => {
    const basePlot = plots?.find(p => p.id === 'magnitude_response');
    if (!basePlot || numPoints === 0) return basePlot;

    const idx = currentIndex;
    const traces = [];

    // Full curve faded (ghost)
    traces.push({
      x: omega,
      y: magnitude,
      type: 'scatter',
      mode: 'lines',
      line: { color: 'rgba(59, 130, 246, 0.15)', width: 1.5 },
      name: '|H(jω)| (full)',
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Progressive curve
    traces.push({
      x: omega.slice(0, idx + 1),
      y: magnitude.slice(0, idx + 1),
      type: 'scatter',
      mode: 'lines',
      line: { color: '#3b82f6', width: 2.5 },
      name: '|H(jω)|',
      hovertemplate: 'ω = %{x:.2f}<br>|H| = %{y:.3f}<extra></extra>',
    });

    // Current point dot
    traces.push({
      x: [omega[idx]],
      y: [magnitude[idx]],
      type: 'scatter',
      mode: 'markers',
      marker: { symbol: 'circle', size: 8, color: '#10b981', line: { width: 2, color: '#10b981' } },
      name: 'Current ω',
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Individual contributions if enabled
    if (currentParams?.show_individual) {
      (metadata?.individual_zero_mags || []).forEach((zmag, i) => {
        traces.push({
          x: omega.slice(0, idx + 1),
          y: zmag.slice(0, idx + 1),
          type: 'scatter',
          mode: 'lines',
          line: { color: '#14b8a6', width: 1.5, dash: 'dot' },
          name: `|jω − z${i + 1}|`,
          opacity: 0.7,
        });
      });
      (metadata?.individual_pole_mags || []).forEach((pmag, i) => {
        traces.push({
          x: omega.slice(0, idx + 1),
          y: pmag.slice(0, idx + 1),
          type: 'scatter',
          mode: 'lines',
          line: { color: '#ef4444', width: 1.5, dash: 'dot' },
          name: `|jω − p${i + 1}|`,
          opacity: 0.7,
        });
      });
    }

    const baseLayout = basePlot.layout || {};

    return {
      ...basePlot,
      data: traces,
      layout: {
        ...baseLayout,
        showlegend: !!currentParams?.show_individual,
        datarevision: `mag-${idx}-${Date.now()}`,
        uirevision: baseLayout.uirevision,
      },
    };
  }, [plots, currentIndex, omega, magnitude, numPoints, metadata, currentParams?.show_individual]);

  // Build phase plot with progressive reveal
  const phasePlotAnimated = useMemo(() => {
    const basePlot = plots?.find(p => p.id === 'phase_response');
    if (!basePlot || numPoints === 0) return basePlot;

    const idx = currentIndex;
    const traces = [];

    // Full curve faded
    traces.push({
      x: omega,
      y: phase,
      type: 'scatter',
      mode: 'lines',
      line: { color: 'rgba(239, 68, 68, 0.15)', width: 1.5 },
      name: '∠H(jω) (full)',
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Progressive curve
    traces.push({
      x: omega.slice(0, idx + 1),
      y: phase.slice(0, idx + 1),
      type: 'scatter',
      mode: 'lines',
      line: { color: '#ef4444', width: 2.5 },
      name: '∠H(jω)',
      hovertemplate: 'ω = %{x:.2f}<br>∠H = %{y:.3f} rad<extra></extra>',
    });

    // Current point dot
    traces.push({
      x: [omega[idx]],
      y: [phase[idx]],
      type: 'scatter',
      mode: 'markers',
      marker: { symbol: 'circle', size: 8, color: '#10b981', line: { width: 2, color: '#10b981' } },
      name: 'Current ω',
      showlegend: false,
      hoverinfo: 'skip',
    });

    // Individual phase contributions
    if (currentParams?.show_individual) {
      (metadata?.individual_zero_phases || []).forEach((zph, i) => {
        traces.push({
          x: omega.slice(0, idx + 1),
          y: zph.slice(0, idx + 1),
          type: 'scatter',
          mode: 'lines',
          line: { color: '#14b8a6', width: 1.5, dash: 'dot' },
          name: `∠(jω − z${i + 1})`,
          opacity: 0.7,
        });
      });
      (metadata?.individual_pole_phases || []).forEach((pph, i) => {
        const negated = pph.slice(0, idx + 1).map(v => -v);
        traces.push({
          x: omega.slice(0, idx + 1),
          y: negated,
          type: 'scatter',
          mode: 'lines',
          line: { color: '#ef4444', width: 1.5, dash: 'dot' },
          name: `−∠(jω − p${i + 1})`,
          opacity: 0.7,
        });
      });
    }

    const baseLayout = basePlot.layout || {};

    return {
      ...basePlot,
      data: traces,
      layout: {
        ...baseLayout,
        showlegend: !!currentParams?.show_individual,
        datarevision: `phase-${idx}-${Date.now()}`,
        uirevision: baseLayout.uirevision,
      },
    };
  }, [plots, currentIndex, omega, phase, numPoints, metadata, currentParams?.show_individual]);

  // Individual vector contribution cards
  const individualCards = useMemo(() => {
    if (!currentParams?.show_individual || numPoints === 0) return null;

    const idx = currentIndex;
    const cards = [];

    zeros.forEach((z, i) => {
      const mag = (metadata?.individual_zero_mags?.[i] || [])[idx] || 0;
      const ph = (metadata?.individual_zero_phases?.[i] || [])[idx] || 0;
      cards.push(
        <div key={`z${i}`} className="vfr-individual-card">
          <div className="vfr-individual-card-header">
            <div className="vfr-dot zero" />
            <span>Zero {i + 1}: s = {z.real.toFixed(2)}{z.imag !== 0 ? ` ${z.imag >= 0 ? '+' : '−'} ${Math.abs(z.imag).toFixed(2)}j` : ''}</span>
          </div>
          <div className="vfr-individual-values">
            <span>|jω − z| = <strong>{mag.toFixed(3)}</strong></span>
            <span>∠(jω − z) = <strong>{ph.toFixed(3)} rad</strong></span>
          </div>
        </div>
      );
    });

    poles.forEach((p, i) => {
      const mag = (metadata?.individual_pole_mags?.[i] || [])[idx] || 0;
      const ph = (metadata?.individual_pole_phases?.[i] || [])[idx] || 0;
      cards.push(
        <div key={`p${i}`} className="vfr-individual-card">
          <div className="vfr-individual-card-header">
            <div className="vfr-dot pole" />
            <span>Pole {i + 1}: s = {p.real.toFixed(2)}{p.imag !== 0 ? ` ${p.imag >= 0 ? '+' : '−'} ${Math.abs(p.imag).toFixed(2)}j` : ''}</span>
          </div>
          <div className="vfr-individual-values">
            <span>|jω − p| = <strong>{mag.toFixed(3)}</strong></span>
            <span>−∠(jω − p) = <strong>{(-ph).toFixed(3)} rad</strong></span>
          </div>
        </div>
      );
    });

    return cards;
  }, [currentParams?.show_individual, currentIndex, currentOmega, zeros, poles, metadata, numPoints]);

  if (!metadata || numPoints === 0) {
    return <PlotDisplay plots={plots} isLoading={!metadata} emptyMessage="Loading vector diagram..." />;
  }

  return (
    <div className="vfr-viewer">
      {/* TF Input Banner */}
      <TransferFunctionBanner
        metadata={metadata}
        onParseExpression={handleParseExpression}
      />

      {/* S-Plane — FULL WIDTH */}
      <div className="vfr-splane-container">
        {sPlaneWithVectors && (
          <PlotDisplay plots={[sPlaneWithVectors]} />
        )}
      </div>

      {/* Magnitude + Phase side-by-side */}
      <div className="vfr-response-row">
        <div className="vfr-plot-wrapper">
          {magPlotAnimated && (
            <PlotDisplay plots={[magPlotAnimated]} />
          )}
        </div>
        <div className="vfr-plot-wrapper">
          {phasePlotAnimated && (
            <PlotDisplay plots={[phasePlotAnimated]} />
          )}
        </div>
      </div>

      {/* Animation controls */}
      <div className="vfr-controls-bar" role="toolbar" aria-label="Animation controls">
        <div className="vfr-transport-buttons">
          <button className="vfr-btn" onClick={stepBack} aria-label="Step backward" title="Step backward">
            &#x23EA;
          </button>
          <button
            className={`vfr-btn play-btn ${isPlaying ? 'active' : ''}`}
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            title={isPlaying ? 'Pause sweep' : 'Play sweep'}
          >
            {isPlaying ? '\u23F8' : '\u25B6'}
          </button>
          <button className="vfr-btn" onClick={stepForward} aria-label="Step forward" title="Step forward">
            &#x23E9;
          </button>
        </div>

        <div className="vfr-omega-slider-group">
          <label htmlFor="omega-scrub">ω</label>
          <input
            id="omega-scrub"
            className="vfr-omega-slider"
            type="range"
            min={0}
            max={numPoints - 1}
            value={currentIndex}
            onChange={handleSliderChange}
            aria-label="Frequency position"
          />
        </div>

        <div className="vfr-speed-group">
          <label htmlFor="speed-select">Speed</label>
          <select
            id="speed-select"
            className="vfr-speed-select"
            value={speed}
            onChange={handleSpeedChange}
            aria-label="Animation speed"
          >
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
          </select>
        </div>
      </div>

      {/* Current values readout */}
      <div className="vfr-info-readout" aria-live="polite">
        <div className="vfr-info-item">
          <span className="vfr-info-label">ω =</span>
          <span className="vfr-info-value">{currentOmega.toFixed(2)} rad/s</span>
        </div>
        <div className="vfr-info-divider" />
        <div className="vfr-info-item">
          <span className="vfr-info-label">|H(jω)| =</span>
          <span className="vfr-info-value">{currentMag.toFixed(3)}</span>
        </div>
        <div className="vfr-info-divider" />
        <div className="vfr-info-item">
          <span className="vfr-info-label">∠H(jω) =</span>
          <span className="vfr-info-value">{currentPhase.toFixed(3)} rad</span>
        </div>
        {gain !== 1 && (
          <>
            <div className="vfr-info-divider" />
            <div className="vfr-info-item">
              <span className="vfr-info-label">K =</span>
              <span className="vfr-info-value">{gain}</span>
            </div>
          </>
        )}
      </div>

      {/* Individual contributions (when enabled) */}
      {individualCards && individualCards.length > 0 && (
        <div className="vfr-individual-section">
          <div className="vfr-individual-title">Individual Vector Contributions at ω = {currentOmega.toFixed(2)}</div>
          <div className="vfr-individual-grid">
            {individualCards}
          </div>
        </div>
      )}
    </div>
  );
}

export default VectorFreqResponseViewer;
