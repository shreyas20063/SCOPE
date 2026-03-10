/**
 * NyquistBodeViewer
 *
 * Side-by-side comparison of Bode (magnitude + phase) and Nyquist plots.
 * Features:
 * - Animated frequency sweep with play/pause/scrub
 * - Hover-based cross-highlighting across all plots
 * - Stability info banner (gain margin, phase margin)
 * - Pole-zero map
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import Plot from 'react-plotly.js';
import './NyquistBodeViewer.css';

const FRAME_INTERVAL_BASE = 40; // ~25fps

/* ──────────────────────────────────────────────
   Stability Banner
   ────────────────────────────────────────────── */
function StabilityBanner({ stabilityInfo }) {
  if (!stabilityInfo) return null;
  const { gain_margin_db, phase_margin_deg, gain_crossover_freq, phase_crossover_freq, stability_status } = stabilityInfo;

  const cls = stability_status === 'Stable' ? 'stable'
    : stability_status === 'Unstable' ? 'unstable' : 'marginal';

  const fmtVal = (v, unit) => v != null ? `${v}${unit}` : '∞';

  return (
    <div className={`nbc-stability-banner ${cls}`}>
      <span className="nbc-stability-badge">{stability_status}</span>
      <div className="nbc-margins">
        <span className="nbc-margin-item">
          <span className="nbc-margin-label">GM:</span>
          <span className="nbc-margin-value">{fmtVal(gain_margin_db, ' dB')}</span>
        </span>
        <span className="nbc-margin-item">
          <span className="nbc-margin-label">PM:</span>
          <span className="nbc-margin-value">{fmtVal(phase_margin_deg, '°')}</span>
        </span>
        {gain_crossover_freq != null && (
          <span className="nbc-margin-item">
            <span className="nbc-margin-label">ω_gc:</span>
            <span className="nbc-margin-value">{gain_crossover_freq.toFixed(2)} rad/s</span>
          </span>
        )}
        {phase_crossover_freq != null && (
          <span className="nbc-margin-item">
            <span className="nbc-margin-label">ω_pc:</span>
            <span className="nbc-margin-value">{phase_crossover_freq.toFixed(2)} rad/s</span>
          </span>
        )}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Main Viewer
   ────────────────────────────────────────────── */
function NyquistBodeViewer({ metadata, plots, currentParams, onParamChange }) {
  // Animation state
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const animFrameRef = useRef(null);
  const lastFrameTimeRef = useRef(0);
  const indexRef = useRef(0);

  // Extract metadata arrays for sync highlighting
  const omega = metadata?.omega || [];
  const magDb = metadata?.magnitude_db || [];
  const phaseDeg = metadata?.phase_deg || [];
  const nyqReal = metadata?.nyquist_real || [];
  const nyqImag = metadata?.nyquist_imag || [];
  const numPoints = omega.length;

  // Active index: animation index or hovered index
  const activeIndex = hoveredIndex != null ? hoveredIndex : (isPlaying || currentIndex > 0 ? currentIndex : null);

  // Find plots by ID
  const bodeMagPlot = plots?.find(p => p.id === 'bode_magnitude');
  const bodePhasePlot = plots?.find(p => p.id === 'bode_phase');
  const nyquistPlot = plots?.find(p => p.id === 'nyquist');
  const pzPlot = plots?.find(p => p.id === 'pole_zero');

  // Reset animation when system changes
  const fingerprint = useMemo(() => {
    return `${metadata?.preset_name}-${metadata?.tf_expression}-${JSON.stringify(metadata?.poles)}`;
  }, [metadata?.preset_name, metadata?.tf_expression, metadata?.poles]);

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

  // Hover handlers for cross-plot sync
  const handlePlotHover = useCallback((event) => {
    if (event?.points?.[0]?.pointIndex != null) {
      setHoveredIndex(event.points[0].pointIndex);
    }
  }, []);

  const handlePlotUnhover = useCallback(() => {
    setHoveredIndex(null);
  }, []);

  // Transport controls
  const togglePlay = () => setIsPlaying(prev => !prev);
  const stepBack = () => {
    setIsPlaying(false);
    setCurrentIndex(prev => Math.max(0, prev - 5));
  };
  const stepForward = () => {
    setIsPlaying(false);
    setCurrentIndex(prev => Math.min(numPoints - 1, prev + 5));
  };
  const handleScrub = (e) => {
    const val = parseInt(e.target.value, 10);
    setCurrentIndex(val);
    indexRef.current = val;
  };

  // Build highlight marker for Bode magnitude
  const bodeMagWithHighlight = useMemo(() => {
    if (!bodeMagPlot) return null;
    const data = [...bodeMagPlot.data];
    if (activeIndex != null && activeIndex < numPoints) {
      data.push({
        x: [omega[activeIndex]],
        y: [magDb[activeIndex]],
        type: 'scatter',
        mode: 'markers',
        marker: { color: '#fbbf24', size: 12, symbol: 'circle',
                  line: { color: '#fff', width: 2 } },
        name: `ω = ${omega[activeIndex]?.toFixed(2)}`,
        showlegend: false,
        hoverinfo: 'skip',
      });
    }
    return data;
  }, [bodeMagPlot, activeIndex, omega, magDb, numPoints]);

  // Build highlight marker for Bode phase
  const bodePhaseWithHighlight = useMemo(() => {
    if (!bodePhasePlot) return null;
    const data = [...bodePhasePlot.data];
    if (activeIndex != null && activeIndex < numPoints) {
      data.push({
        x: [omega[activeIndex]],
        y: [phaseDeg[activeIndex]],
        type: 'scatter',
        mode: 'markers',
        marker: { color: '#fbbf24', size: 12, symbol: 'circle',
                  line: { color: '#fff', width: 2 } },
        showlegend: false,
        hoverinfo: 'skip',
      });
    }
    return data;
  }, [bodePhasePlot, activeIndex, omega, phaseDeg, numPoints]);

  // Build highlight for Nyquist + magnitude/angle line from origin
  const nyquistWithHighlight = useMemo(() => {
    if (!nyquistPlot) return null;
    const data = [...nyquistPlot.data];
    if (activeIndex != null && activeIndex < numPoints) {
      const re = nyqReal[activeIndex];
      const im = nyqImag[activeIndex];
      if (re != null && im != null && isFinite(re) && isFinite(im)) {
        // Line from origin to highlighted point
        data.push({
          x: [0, re],
          y: [0, im],
          type: 'scatter',
          mode: 'lines',
          line: { color: '#fbbf24', width: 2, dash: 'dash' },
          showlegend: false,
          hoverinfo: 'skip',
        });
        // Highlighted point
        data.push({
          x: [re],
          y: [im],
          type: 'scatter',
          mode: 'markers',
          marker: { color: '#fbbf24', size: 12, symbol: 'circle',
                    line: { color: '#fff', width: 2 } },
          showlegend: false,
          hoverinfo: 'skip',
        });
      }
    }
    return data;
  }, [nyquistPlot, activeIndex, nyqReal, nyqImag, numPoints]);

  // Plotly config
  const plotConfig = { responsive: true, displayModeBar: false };

  // Build layouts with datarevision to force updates
  const makeBodeLayout = (plot, id) => {
    if (!plot) return {};
    return {
      ...plot.layout,
      datarevision: `${id}-${Date.now()}`,
      uirevision: id,
      autosize: true,
      height: 220,
    };
  };

  const nyquistLayout = useMemo(() => {
    if (!nyquistPlot) return {};
    return {
      ...nyquistPlot.layout,
      datarevision: `nyquist-${Date.now()}`,
      uirevision: 'nyquist',
      autosize: true,
      height: 456,
    };
  }, [nyquistPlot, activeIndex]);

  const pzLayout = useMemo(() => {
    if (!pzPlot) return {};
    return {
      ...pzPlot.layout,
      datarevision: `pz-${Date.now()}`,
      uirevision: 'pole_zero',
      autosize: true,
      height: 220,
    };
  }, [pzPlot]);

  // Current frequency readout
  const freqReadout = activeIndex != null && activeIndex < numPoints
    ? `ω = ${omega[activeIndex]?.toFixed(3)} rad/s | |H| = ${magDb[activeIndex]?.toFixed(1)} dB | ∠H = ${phaseDeg[activeIndex]?.toFixed(1)}°`
    : '';

  return (
    <div className="nyquist-bode-viewer">
      {/* Stability Banner */}
      <StabilityBanner stabilityInfo={metadata?.stability_info} />

      {/* TF Expression */}
      {metadata?.tf_expression && (
        <div className="nbc-tf-expression">{metadata.tf_expression}</div>
      )}

      {/* Animation Controls */}
      {numPoints > 0 && (
        <div className="nbc-animation-controls">
          <button className="nbc-transport-btn" onClick={stepBack} title="Step back">⏪</button>
          <button className={`nbc-transport-btn ${isPlaying ? 'active' : ''}`} onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
            {isPlaying ? '⏸' : '▶'}
          </button>
          <button className="nbc-transport-btn" onClick={stepForward} title="Step forward">⏩</button>
          <input
            type="range"
            className="nbc-scrubber"
            min={0}
            max={numPoints - 1}
            value={currentIndex}
            onChange={handleScrub}
          />
          <select className="nbc-speed-select" value={speed} onChange={e => setSpeed(parseFloat(e.target.value))}>
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
          </select>
          <span className="nbc-freq-readout">{freqReadout}</span>
        </div>
      )}

      {/* Main Plot Grid: Bode left, Nyquist right */}
      <div className="nbc-plot-grid">
        <div className="nbc-bode-column">
          {/* Bode Magnitude */}
          {bodeMagPlot && (
            <div className="nbc-plot-cell">
              <Plot
                data={bodeMagWithHighlight}
                layout={makeBodeLayout(bodeMagPlot, 'bode_mag')}
                config={plotConfig}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                onHover={handlePlotHover}
                onUnhover={handlePlotUnhover}
              />
            </div>
          )}
          {/* Bode Phase */}
          {bodePhasePlot && (
            <div className="nbc-plot-cell">
              <Plot
                data={bodePhaseWithHighlight}
                layout={makeBodeLayout(bodePhasePlot, 'bode_phase')}
                config={plotConfig}
                style={{ width: '100%', height: '100%' }}
                useResizeHandler
                onHover={handlePlotHover}
                onUnhover={handlePlotUnhover}
              />
            </div>
          )}
        </div>

        {/* Nyquist Plot */}
        {nyquistPlot && (
          <div className="nbc-plot-cell nbc-nyquist-cell">
            <Plot
              data={nyquistWithHighlight}
              layout={nyquistLayout}
              config={plotConfig}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
              onHover={handlePlotHover}
              onUnhover={handlePlotUnhover}
            />
          </div>
        )}
      </div>

      {/* Pole-Zero Map */}
      {pzPlot && (
        <div className="nbc-pz-row">
          <Plot
            data={pzPlot.data}
            layout={pzLayout}
            config={plotConfig}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        </div>
      )}
    </div>
  );
}

export default NyquistBodeViewer;
