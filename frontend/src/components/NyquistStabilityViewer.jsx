/**
 * NyquistStabilityViewer
 *
 * Educational tool for the Nyquist Stability Criterion:
 * - D-contour visualization in s-plane with OL poles/zeros
 * - Nyquist plot with encirclement counting of (-1, 0)
 * - N = Z - P equation with live computed values
 * - Closed-loop pole map confirming Z count
 * - Synchronized animation: dot on D-contour + image on Nyquist
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import Plot from 'react-plotly.js';
import './NyquistStabilityViewer.css';

const FRAME_INTERVAL_BASE = 40; // ~25fps

/* ──────────────────────────────────────────────
   Criterion Banner — N = Z - P with values
   ────────────────────────────────────────────── */
function CriterionBanner({ criterion, stabilityInfo }) {
  if (!criterion) return null;
  const { P, Z, N, stability_status } = criterion;

  const cls = stability_status === 'Stable' ? 'stable'
    : stability_status === 'Unstable' ? 'unstable' : 'marginal';

  const fmtVal = (v, unit) => v != null ? `${v}${unit}` : '\u221e';

  return (
    <div className={`nsc-criterion-banner ${cls}`}>
      <span className="nsc-stability-badge">{stability_status}</span>
      <div className="nsc-equation">
        <span>N</span>
        <span>=</span>
        <span className="nsc-equation-value">{N}</span>
        <span>=</span>
        <span>Z</span>
        <span className="nsc-equation-value">{Z}</span>
        <span>\u2212</span>
        <span>P</span>
        <span className="nsc-equation-value">{P}</span>
      </div>
      {stabilityInfo && (
        <div className="nsc-margins">
          {stabilityInfo.gain_margin_db != null && (
            <span className="nsc-margin-item">
              <span className="nsc-margin-label">GM:</span>
              <span className="nsc-margin-value">{fmtVal(stabilityInfo.gain_margin_db, ' dB')}</span>
            </span>
          )}
          {stabilityInfo.phase_margin_deg != null && (
            <span className="nsc-margin-item">
              <span className="nsc-margin-label">PM:</span>
              <span className="nsc-margin-value">{fmtVal(stabilityInfo.phase_margin_deg, '\u00b0')}</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────
   Main Viewer
   ────────────────────────────────────────────── */
function NyquistStabilityViewer({ metadata, plots, currentParams, onParamChange }) {
  // Animation state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const animFrameRef = useRef(null);
  const lastFrameTimeRef = useRef(0);
  const indexRef = useRef(0);

  // Extract metadata arrays
  const dContourSReal = metadata?.d_contour_s_real || [];
  const dContourSImag = metadata?.d_contour_s_imag || [];
  const dContourImageReal = metadata?.d_contour_image_real || [];
  const dContourImageImag = metadata?.d_contour_image_imag || [];
  const numPoints = dContourSReal.length;

  // Active index for animation/hover
  const activeIndex = hoveredIndex != null ? hoveredIndex : (isPlaying || currentIndex > 0 ? currentIndex : null);

  // Find plots by ID
  const nyquistPlot = plots?.find(p => p.id === 'nyquist_plot');
  const dContourPlot = plots?.find(p => p.id === 'd_contour_plot');
  const clPolePlot = plots?.find(p => p.id === 'cl_pole_map');

  // Reset animation when system changes
  const fingerprint = useMemo(() => {
    return `${metadata?.preset_name}-${metadata?.tf_expression}-${JSON.stringify(metadata?.ol_poles)}`;
  }, [metadata?.preset_name, metadata?.tf_expression, metadata?.ol_poles]);

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
    return () => { active = false; cancelAnimationFrame(animFrameRef.current); };
  }, [isPlaying, speed, numPoints]);

  // Transport controls
  const togglePlay = () => setIsPlaying(prev => !prev);
  const stepBack = () => {
    setIsPlaying(false);
    setCurrentIndex(prev => Math.max(0, prev - 3));
  };
  const stepForward = () => {
    setIsPlaying(false);
    setCurrentIndex(prev => Math.min(numPoints - 1, prev + 3));
  };
  const handleScrub = (e) => {
    const val = parseInt(e.target.value, 10);
    setCurrentIndex(val);
    indexRef.current = val;
  };

  // D-contour with animated dot
  const dContourWithDot = useMemo(() => {
    if (!dContourPlot) return null;
    const data = [...dContourPlot.data];
    if (activeIndex != null && activeIndex < numPoints) {
      const re = dContourSReal[activeIndex];
      const im = dContourSImag[activeIndex];
      if (re != null && im != null && isFinite(re) && isFinite(im)) {
        data.push({
          x: [re],
          y: [im],
          type: 'scatter',
          mode: 'markers',
          marker: { color: '#fbbf24', size: 14, symbol: 'circle',
                    line: { color: '#fff', width: 2 } },
          name: 'Current point',
          showlegend: false,
          hoverinfo: 'skip',
        });
      }
    }
    return data;
  }, [dContourPlot, activeIndex, dContourSReal, dContourSImag, numPoints]);

  // Nyquist with animated dot + line from origin
  const nyquistWithDot = useMemo(() => {
    if (!nyquistPlot) return null;
    const data = [...nyquistPlot.data];
    if (activeIndex != null && activeIndex < numPoints) {
      const re = dContourImageReal[activeIndex];
      const im = dContourImageImag[activeIndex];
      if (re != null && im != null && isFinite(re) && isFinite(im)) {
        // Line from (-1,0) to point to show encirclement
        data.push({
          x: [-1, re],
          y: [0, im],
          type: 'scatter',
          mode: 'lines',
          line: { color: '#fbbf24', width: 1.5, dash: 'dash' },
          showlegend: false,
          hoverinfo: 'skip',
        });
        // Highlighted point
        data.push({
          x: [re],
          y: [im],
          type: 'scatter',
          mode: 'markers',
          marker: { color: '#fbbf24', size: 14, symbol: 'circle',
                    line: { color: '#fff', width: 2 } },
          showlegend: false,
          hoverinfo: 'skip',
        });
      }
    }
    return data;
  }, [nyquistPlot, activeIndex, dContourImageReal, dContourImageImag, numPoints]);

  // Plotly config
  const plotConfig = { responsive: true, displayModeBar: false };

  // Layouts with datarevision
  const dContourLayout = useMemo(() => {
    if (!dContourPlot) return {};
    return {
      ...dContourPlot.layout,
      datarevision: `dcontour-${Date.now()}`,
      uirevision: 'd_contour',
      autosize: true,
      height: 380,
    };
  }, [dContourPlot, activeIndex]);

  const nyquistLayout = useMemo(() => {
    if (!nyquistPlot) return {};
    return {
      ...nyquistPlot.layout,
      datarevision: `nyquist-${Date.now()}`,
      uirevision: 'nyquist',
      autosize: true,
      height: 380,
    };
  }, [nyquistPlot, activeIndex]);

  const clPoleLayout = useMemo(() => {
    if (!clPolePlot) return {};
    return {
      ...clPolePlot.layout,
      datarevision: `clpoles-${Date.now()}`,
      uirevision: 'cl_poles',
      autosize: true,
      height: 260,
    };
  }, [clPolePlot]);

  // Frequency readout
  const freqReadout = activeIndex != null && activeIndex < numPoints
    ? `s = ${dContourSReal[activeIndex]?.toFixed(3)} + ${dContourSImag[activeIndex]?.toFixed(3)}j`
    : '';

  const criterion = metadata?.stability_criterion;
  const stabilityInfo = metadata?.stability_info;

  return (
    <div className="nyquist-stability-viewer">
      {/* Criterion Banner: N = Z - P */}
      <CriterionBanner criterion={criterion} stabilityInfo={stabilityInfo} />

      {/* Explanation */}
      {criterion?.explanation && (
        <div className="nsc-explanation">{criterion.explanation}</div>
      )}

      {/* TF Expression */}
      {metadata?.tf_expression && (
        <div className="nsc-tf-expression">{metadata.tf_expression}</div>
      )}

      {/* Animation Controls */}
      {numPoints > 0 && (
        <div className="nsc-animation-controls">
          <button className="nsc-transport-btn" onClick={stepBack} title="Step back">\u23ea</button>
          <button className={`nsc-transport-btn ${isPlaying ? 'active' : ''}`} onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
            {isPlaying ? '\u23f8' : '\u25b6'}
          </button>
          <button className="nsc-transport-btn" onClick={stepForward} title="Step forward">\u23e9</button>
          <input
            type="range"
            className="nsc-scrubber"
            min={0}
            max={numPoints - 1}
            value={currentIndex}
            onChange={handleScrub}
          />
          <select className="nsc-speed-select" value={speed} onChange={e => setSpeed(parseFloat(e.target.value))}>
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
          </select>
          <span className="nsc-freq-readout">{freqReadout}</span>
        </div>
      )}

      {/* Main Plot Grid: D-contour left, Nyquist right */}
      <div className="nsc-plot-grid">
        {/* D-Contour (S-plane) */}
        {dContourPlot && (
          <div className="nsc-plot-cell">
            <Plot
              data={dContourWithDot}
              layout={dContourLayout}
              config={plotConfig}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </div>
        )}

        {/* Nyquist Plot */}
        {nyquistPlot && (
          <div className="nsc-plot-cell">
            <Plot
              data={nyquistWithDot}
              layout={nyquistLayout}
              config={plotConfig}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </div>
        )}
      </div>

      {/* Closed-Loop Pole Map */}
      {clPolePlot && (
        <div className="nsc-cl-row">
          <Plot
            data={clPolePlot.data}
            layout={clPoleLayout}
            config={plotConfig}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        </div>
      )}
    </div>
  );
}

export default NyquistStabilityViewer;
