/**
 * AudioFreqResponseViewer - Filter Design Tool
 *
 * Split-layout custom viewer for audio_freq_response simulation.
 * Left: Interactive SVG s-plane with drag-to-move poles/zeros
 * Right: Magnitude + Phase Plotly plots
 * Bottom: Toolbar, TF input, preset cards, collapsible time/spectrum
 */

import React, { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/AudioFreqResponseViewer.css';

// ─────────────────────────────────────────────────
// SVG S-Plane Component (redesigned)
// ─────────────────────────────────────────────────

const SVG_W = 600;
const SVG_H = 500;
const PAD = 50;

function SPlaneCanvas({ poles, zeros, placementMode, range, onAddAtClick, onRemovePole, onRemoveZero, onMovePole, onMoveZero, isUpdating }) {
  const svgRef = useRef(null);
  const [hover, setHover] = useState(null); // {svgX, svgY, sigma, omega}
  const [dragging, setDragging] = useState(null); // {type: 'pole'|'zero', index, startX, startY}
  const dragMoved = useRef(false);

  // Coordinate transforms
  const toSvgX = useCallback((sigma) => PAD + ((sigma + range) / (2 * range)) * (SVG_W - 2 * PAD), [range]);
  const toSvgY = useCallback((omega) => PAD + ((range - omega) / (2 * range)) * (SVG_H - 2 * PAD), [range]);
  const toSigma = useCallback((svgX) => ((svgX - PAD) / (SVG_W - 2 * PAD)) * (2 * range) - range, [range]);
  const toOmega = useCallback((svgY) => range - ((svgY - PAD) / (SVG_H - 2 * PAD)) * (2 * range), [range]);

  // Smart snap: snap to grid step based on range, not to integers
  const snapStep = useMemo(() => {
    if (range <= 50) return 1;
    if (range <= 200) return 5;
    if (range <= 500) return 10;
    if (range <= 2000) return 50;
    if (range <= 5000) return 100;
    return 500;
  }, [range]);

  const snapValue = useCallback((val) => {
    // Snap to zero if very close
    if (Math.abs(val) < range * 0.02) return 0;
    return Math.round(val / snapStep) * snapStep;
  }, [range, snapStep]);

  const getSvgCoords = useCallback((e) => {
    const svg = svgRef.current;
    if (!svg) return null;
    const rect = svg.getBoundingClientRect();
    const svgX = ((e.clientX - rect.left) / rect.width) * SVG_W;
    const svgY = ((e.clientY - rect.top) / rect.height) * SVG_H;
    return { svgX, svgY };
  }, []);

  // Mouse move: hover crosshair + drag
  const handleMouseMove = useCallback((e) => {
    const coords = getSvgCoords(e);
    if (!coords) return;
    const { svgX, svgY } = coords;

    const sigma = toSigma(svgX);
    const omega = toOmega(svgY);
    const inBounds = svgX >= PAD && svgX <= SVG_W - PAD && svgY >= PAD && svgY <= SVG_H - PAD;

    if (inBounds) {
      setHover({ svgX, svgY, sigma, omega });
    } else {
      setHover(null);
    }

    if (dragging) {
      dragMoved.current = true;
      // Update is visual only during drag — we send the final position on mouseUp
    }
  }, [getSvgCoords, toSigma, toOmega, dragging]);

  const handleMouseLeave = useCallback(() => {
    setHover(null);
    if (dragging) {
      // Cancel drag if mouse leaves
      setDragging(null);
      dragMoved.current = false;
    }
  }, [dragging]);

  // Click to add pole/zero (only if not dragging)
  const handleClick = useCallback((e) => {
    if (isUpdating || dragMoved.current) return;
    const coords = getSvgCoords(e);
    if (!coords) return;
    const { svgX, svgY } = coords;
    if (svgX < PAD || svgX > SVG_W - PAD || svgY < PAD || svgY > SVG_H - PAD) return;

    const sigma = snapValue(toSigma(svgX));
    const omega = snapValue(toOmega(svgY));
    onAddAtClick(sigma, omega);
  }, [isUpdating, getSvgCoords, snapValue, toSigma, toOmega, onAddAtClick]);

  // Drag start on pole/zero marker
  const handleMarkerMouseDown = useCallback((e, type, index) => {
    e.stopPropagation();
    e.preventDefault();
    dragMoved.current = false;
    setDragging({ type, index });
  }, []);

  // Drag end — send move action to backend
  const handleMouseUp = useCallback((e) => {
    if (dragging && dragMoved.current && hover) {
      const sigma = snapValue(hover.sigma);
      const omega = snapValue(hover.omega);
      if (dragging.type === 'pole') {
        onMovePole(dragging.index, sigma, omega);
      } else {
        onMoveZero(dragging.index, sigma, omega);
      }
    }
    setDragging(null);
    dragMoved.current = false;
  }, [dragging, hover, snapValue, onMovePole, onMoveZero]);

  // Right-click to remove
  const handleContextMenu = useCallback((e, type, index) => {
    e.preventDefault();
    e.stopPropagation();
    if (type === 'pole') onRemovePole(index);
    else onRemoveZero(index);
  }, [onRemovePole, onRemoveZero]);

  // Grid lines
  const gridLines = useMemo(() => {
    const lines = [];
    const step = snapStep * 2 > range ? snapStep : snapStep * 2;
    for (let v = -Math.floor(range / step) * step; v <= range; v += step) {
      if (v === 0) continue;
      lines.push(
        <line key={`gv${v}`} className="grid-line"
          x1={toSvgX(v)} y1={PAD} x2={toSvgX(v)} y2={SVG_H - PAD} />
      );
      lines.push(
        <line key={`gh${v}`} className="grid-line"
          x1={PAD} y1={toSvgY(v)} x2={SVG_W - PAD} y2={toSvgY(v)} />
      );
    }
    return lines;
  }, [range, snapStep, toSvgX, toSvgY]);

  // Axis tick labels
  const tickLabels = useMemo(() => {
    const labels = [];
    const step = snapStep * 2 > range ? snapStep : snapStep * 2;
    const formatVal = (v) => {
      if (Math.abs(v) >= 1000) return `${(v/1000).toFixed(v % 1000 === 0 ? 0 : 1)}k`;
      return String(v);
    };
    for (let v = -Math.floor(range / step) * step; v <= range; v += step) {
      if (v === 0) continue;
      const sx = toSvgX(v);
      const sy = toSvgY(v);
      if (sx > PAD + 15 && sx < SVG_W - PAD - 15) {
        labels.push(
          <text key={`lx${v}`} className="axis-label" x={sx} y={SVG_H - PAD + 16} textAnchor="middle">
            {formatVal(v)}
          </text>
        );
      }
      if (sy > PAD + 15 && sy < SVG_H - PAD - 15) {
        labels.push(
          <text key={`ly${v}`} className="axis-label" x={PAD - 8} y={sy + 4} textAnchor="end">
            {formatVal(v)}
          </text>
        );
      }
    }
    return labels;
  }, [range, snapStep, toSvgX, toSvgY]);

  // Conjugate pair connecting lines
  const conjugateLines = useMemo(() => {
    const lines = [];
    const drawConjugates = (items, prefix) => {
      const seen = new Set();
      items.forEach((p, i) => {
        if (seen.has(i) || Math.abs(p.imag) < 1) return;
        items.forEach((p2, j) => {
          if (j <= i || seen.has(j)) return;
          if (Math.abs(p.real - p2.real) < 1 && Math.abs(p.imag + p2.imag) < 1) {
            seen.add(i);
            seen.add(j);
            lines.push(
              <line key={`c${prefix}${i}-${j}`} className="conjugate-line"
                x1={toSvgX(p.real)} y1={toSvgY(p.imag)}
                x2={toSvgX(p2.real)} y2={toSvgY(p2.imag)} />
            );
          }
        });
      });
    };
    drawConjugates(poles || [], 'p');
    drawConjugates(zeros || [], 'z');
    return lines;
  }, [poles, zeros, toSvgX, toSvgY]);

  const markerSize = 11;
  const hitSize = 20; // invisible hit area

  // Get visual position for a marker (during drag, use hover position)
  const getMarkerPos = useCallback((type, index, item) => {
    if (dragging && dragging.type === type && dragging.index === index && hover && dragMoved.current) {
      return { x: hover.svgX, y: hover.svgY };
    }
    return { x: toSvgX(item.real), y: toSvgY(item.imag) };
  }, [dragging, hover, toSvgX, toSvgY]);

  return (
    <div className="afr-splane-container">
      <svg
        ref={svgRef}
        className="afr-splane-svg"
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onMouseUp={handleMouseUp}
        onContextMenu={(e) => e.preventDefault()}
        aria-label={`S-plane. Click to add ${placementMode}. ${(poles || []).length} poles, ${(zeros || []).length} zeros.`}
        role="img"
      >
        {/* Stable region fill (left half-plane) */}
        <rect className="stable-region"
          x={PAD} y={PAD}
          width={toSvgX(0) - PAD} height={SVG_H - 2 * PAD} />

        {/* Grid */}
        {gridLines}

        {/* Real axis (sigma) */}
        <line className="axis-line"
          x1={PAD} y1={toSvgY(0)} x2={SVG_W - PAD} y2={toSvgY(0)} />

        {/* jw axis (imaginary) */}
        <line className="jw-axis"
          x1={toSvgX(0)} y1={PAD} x2={toSvgX(0)} y2={SVG_H - PAD} />

        {/* Axis labels */}
        <text className="axis-title" x={SVG_W - PAD + 5} y={toSvgY(0) + 4} textAnchor="start">σ</text>
        <text className="axis-title" x={toSvgX(0) + 6} y={PAD - 5} textAnchor="start">jω</text>
        {tickLabels}

        {/* Conjugate pair lines */}
        {conjugateLines}

        {/* Hover crosshair */}
        {hover && !dragging && (
          <g className="hover-crosshair">
            <line x1={hover.svgX} y1={PAD} x2={hover.svgX} y2={SVG_H - PAD} />
            <line x1={PAD} y1={hover.svgY} x2={SVG_W - PAD} y2={hover.svgY} />
          </g>
        )}

        {/* Drag crosshair */}
        {dragging && hover && dragMoved.current && (
          <g className="drag-crosshair">
            <line x1={hover.svgX} y1={PAD} x2={hover.svgX} y2={SVG_H - PAD} />
            <line x1={PAD} y1={hover.svgY} x2={SVG_W - PAD} y2={hover.svgY} />
          </g>
        )}

        {/* Zeros (circles) */}
        {(zeros || []).map((z, i) => {
          const pos = getMarkerPos('zero', z.index ?? i, z);
          return (
            <g key={`z${i}`}
              onMouseDown={(e) => handleMarkerMouseDown(e, 'zero', z.index ?? i)}
              onContextMenu={(e) => handleContextMenu(e, 'zero', z.index ?? i)}
              style={{ cursor: dragging ? 'grabbing' : 'grab' }}
            >
              <circle className="hit-area" cx={pos.x} cy={pos.y} r={hitSize} />
              <circle className="zero-marker" cx={pos.x} cy={pos.y} r={markerSize} />
              <title>Zero {i + 1}: σ={z.real.toFixed(1)}, ω={z.imag.toFixed(1)} — Drag to move, right-click to remove</title>
            </g>
          );
        })}

        {/* Poles (X markers) */}
        {(poles || []).map((p, i) => {
          const pos = getMarkerPos('pole', p.index ?? i, p);
          return (
            <g key={`p${i}`}
              onMouseDown={(e) => handleMarkerMouseDown(e, 'pole', p.index ?? i)}
              onContextMenu={(e) => handleContextMenu(e, 'pole', p.index ?? i)}
              style={{ cursor: dragging ? 'grabbing' : 'grab' }}
            >
              <circle className="hit-area" cx={pos.x} cy={pos.y} r={hitSize} />
              <line className="pole-marker"
                x1={pos.x - markerSize} y1={pos.y - markerSize}
                x2={pos.x + markerSize} y2={pos.y + markerSize} />
              <line className="pole-marker"
                x1={pos.x + markerSize} y1={pos.y - markerSize}
                x2={pos.x - markerSize} y2={pos.y + markerSize} />
              <title>Pole {i + 1}: σ={p.real.toFixed(1)}, ω={p.imag.toFixed(1)} — Drag to move, right-click to remove</title>
            </g>
          );
        })}

        {/* Placement mode indicator */}
        <text x={PAD + 6} y={PAD + 14} fill="var(--text-muted)" fontSize="10" fontFamily="Inter, sans-serif">
          Click to add {placementMode === 'pole' ? '× Pole' : '○ Zero'}
        </text>
      </svg>

      {/* Coordinate readout bar */}
      <div className="afr-splane-readout">
        {hover ? (
          <span>σ = {snapValue(hover.sigma).toFixed(1)}, ω = {snapValue(hover.omega).toFixed(1)} rad/s</span>
        ) : (
          <span>Hover over s-plane for coordinates</span>
        )}
        {dragging && <span className="afr-splane-readout__drag">Dragging {dragging.type}</span>}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────
// Main Viewer Component
// ─────────────────────────────────────────────────

function AudioFreqResponseViewer({ metadata, plots, currentParams, onParamChange, onButtonClick, isUpdating }) {
  const poles = metadata?.poles || [];
  const zeros = metadata?.zeros || [];
  const isStable = metadata?.is_stable !== false;
  const hasMarginal = metadata?.has_marginal_poles === true;
  const tfExpression = metadata?.tf_expression || 'H(s) = 1';
  const filterType = metadata?.filter_type || 'flat';
  const presets = metadata?.presets || ['lowpass', 'highpass', 'bandpass', 'notch', 'resonant', 'allpass'];
  const presetDescriptions = metadata?.preset_descriptions || {};
  const sPlaneRange = metadata?.s_plane_range || 2000;
  const errorMsg = metadata?.error;

  // Local state
  const [placementMode, setPlacementMode] = useState('pole');
  const [tfInput, setTfInput] = useState('');
  const [tfError, setTfError] = useState('');
  const [showTimeDomain, setShowTimeDomain] = useState(false);

  // ── Action handlers ──

  const handleAddAtClick = useCallback((real, imag) => {
    if (isUpdating) return;
    onButtonClick('add_at_click', { real, imag, placement_mode: placementMode });
  }, [onButtonClick, isUpdating, placementMode]);

  const handleRemovePole = useCallback((index) => {
    if (isUpdating) return;
    onButtonClick('remove_pole', { index });
  }, [onButtonClick, isUpdating]);

  const handleRemoveZero = useCallback((index) => {
    if (isUpdating) return;
    onButtonClick('remove_zero', { index });
  }, [onButtonClick, isUpdating]);

  const handleMovePole = useCallback((index, real, imag) => {
    if (isUpdating) return;
    onButtonClick('move_pole', { index, real, imag });
  }, [onButtonClick, isUpdating]);

  const handleMoveZero = useCallback((index, real, imag) => {
    if (isUpdating) return;
    onButtonClick('move_zero', { index, real, imag });
  }, [onButtonClick, isUpdating]);

  const handleClearAll = useCallback(() => {
    if (isUpdating) return;
    onButtonClick('clear_all', {});
  }, [onButtonClick, isUpdating]);

  const handleLoadPreset = useCallback((preset) => {
    if (isUpdating) return;
    onButtonClick('load_preset', { preset });
  }, [onButtonClick, isUpdating]);

  const handleParseTf = useCallback(() => {
    if (isUpdating || !tfInput.trim()) return;
    setTfError('');
    onButtonClick('parse_tf', { tf_string: tfInput.trim() });
  }, [onButtonClick, isUpdating, tfInput]);

  const handleTfKeyDown = useCallback((e) => {
    if (e.key === 'Enter') handleParseTf();
  }, [handleParseTf]);

  // Watch for backend parse errors
  useEffect(() => {
    if (errorMsg && errorMsg.toLowerCase().includes('parse')) {
      setTfError(errorMsg);
    }
  }, [errorMsg]);

  // ── Split plots ──

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
        <div className="afr-tf-badges">
          {stabilityBadge}
          {filterBadge}
          <span className="afr-tf-info">
            Order {metadata?.system_order ?? 0} &middot; {poles.length}P {zeros.length}Z &middot; K={metadata?.gain_K ?? 1}
          </span>
        </div>
      </div>

      {/* Error message */}
      {errorMsg && (
        <div className="afr-error" role="alert">{errorMsg}</div>
      )}

      {/* Main split layout: S-plane left, plots right */}
      <div className="afr-split-layout">
        <div className="afr-split-left">
          <SPlaneCanvas
            poles={poles}
            zeros={zeros}
            placementMode={placementMode}
            range={sPlaneRange}
            onAddAtClick={handleAddAtClick}
            onRemovePole={handleRemovePole}
            onRemoveZero={handleRemoveZero}
            onMovePole={handleMovePole}
            onMoveZero={handleMoveZero}
            isUpdating={isUpdating}
          />
        </div>

        <div className="afr-split-right">
          {magPlot && <PlotDisplay plots={[magPlot]} />}
          {phasePlot && <PlotDisplay plots={[phasePlot]} />}
        </div>
      </div>

      {/* Toolbar row */}
      <div className="afr-toolbar" role="toolbar" aria-label="S-plane tools">
        <div className="afr-toolbar__group">
          <button
            className={`afr-toolbar__btn ${placementMode === 'pole' ? 'afr-toolbar__btn--active-pole' : ''}`}
            onClick={() => setPlacementMode('pole')}
            aria-pressed={placementMode === 'pole'}
          >
            × Pole
          </button>
          <button
            className={`afr-toolbar__btn ${placementMode === 'zero' ? 'afr-toolbar__btn--active-zero' : ''}`}
            onClick={() => setPlacementMode('zero')}
            aria-pressed={placementMode === 'zero'}
          >
            ○ Zero
          </button>
          <button
            className="afr-toolbar__btn afr-toolbar__btn--danger"
            onClick={handleClearAll}
            disabled={isUpdating || (poles.length === 0 && zeros.length === 0)}
            aria-label="Clear all poles and zeros"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Transfer function input */}
      <div className="afr-tf-input-row">
        <label className="afr-tf-input-label">H(s) =</label>
        <input
          type="text"
          className="afr-tf-input"
          placeholder="e.g. (s+2)/(s^2+3s+1)"
          value={tfInput}
          onChange={(e) => { setTfInput(e.target.value); setTfError(''); }}
          onKeyDown={handleTfKeyDown}
          disabled={isUpdating}
          aria-label="Enter transfer function expression"
        />
        <button
          className="afr-tf-input-btn"
          onClick={handleParseTf}
          disabled={isUpdating || !tfInput.trim()}
        >
          Apply
        </button>
        {tfError && <span className="afr-tf-input-error">{tfError}</span>}
      </div>

      {/* Preset cards */}
      <div className="afr-presets">
        <span className="afr-presets-label">Presets</span>
        <div className="afr-presets-grid">
          {presets.map(preset => (
            <button key={preset}
              className="afr-preset-card"
              onClick={() => handleLoadPreset(preset)}
              disabled={isUpdating}
            >
              <span className="afr-preset-card__name">
                {preset.charAt(0).toUpperCase() + preset.slice(1)}
              </span>
              {presetDescriptions[preset] && (
                <span className="afr-preset-card__desc">{presetDescriptions[preset]}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Collapsible time domain + spectrum */}
      <details className="afr-collapsible" open={showTimeDomain} onToggle={(e) => setShowTimeDomain(e.target.open)}>
        <summary className="afr-collapsible__summary">
          Time Domain &amp; Spectrum
        </summary>
        <div className="afr-collapsible__content">
          <div className="afr-plots-grid">
            {timePlot && <PlotDisplay plots={[timePlot]} />}
            {spectrumPlot && <PlotDisplay plots={[spectrumPlot]} />}
          </div>
        </div>
      </details>
    </div>
  );
}

export default AudioFreqResponseViewer;
