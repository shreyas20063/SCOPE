/**
 * AudioFreqResponseViewer - Filter Design Tool
 *
 * Split-layout custom viewer for audio_freq_response simulation.
 * Left: Interactive SVG s-plane with drag-to-move poles/zeros
 * Right: Magnitude + Phase Plotly plots
 * Bottom: TF input, preset cards, collapsible time/spectrum
 */

import React, { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/AudioFreqResponseViewer.css';

// ─────────────────────────────────────────────────
// SVG S-Plane Component
// ─────────────────────────────────────────────────

const SVG_SIZE = 520;
const PAD = 50;

function SPlaneCanvas({ poles, zeros, placementMode, range, onAddAtClick, onRemovePole, onRemoveZero, onMovePole, onMoveZero, isUpdating }) {
  const svgRef = useRef(null);
  const [hover, setHover] = useState(null);
  const [dragState, setDragState] = useState(null); // {type, index, currentSigma, currentOmega, moved}
  const isDraggingRef = useRef(false);
  const clickSuppressed = useRef(false);

  // Coordinate transforms (square: same scale for both axes)
  const toSvgX = useCallback((sigma) => PAD + ((sigma + range) / (2 * range)) * (SVG_SIZE - 2 * PAD), [range]);
  const toSvgY = useCallback((omega) => PAD + ((range - omega) / (2 * range)) * (SVG_SIZE - 2 * PAD), [range]);
  const toSigma = useCallback((svgX) => ((svgX - PAD) / (SVG_SIZE - 2 * PAD)) * (2 * range) - range, [range]);
  const toOmega = useCallback((svgY) => range - ((svgY - PAD) / (SVG_SIZE - 2 * PAD)) * (2 * range), [range]);

  // Smart snap
  const snapStep = useMemo(() => {
    if (range <= 10) return 0.5;
    if (range <= 50) return 1;
    if (range <= 200) return 5;
    if (range <= 500) return 10;
    if (range <= 2000) return 50;
    if (range <= 5000) return 100;
    return 500;
  }, [range]);

  const snapValue = useCallback((val) => {
    if (Math.abs(val) < range * 0.025) return 0;
    return Math.round(val / snapStep) * snapStep;
  }, [range, snapStep]);

  const getSvgCoords = useCallback((e) => {
    const svg = svgRef.current;
    if (!svg) return null;
    const rect = svg.getBoundingClientRect();
    return {
      svgX: ((e.clientX - rect.left) / rect.width) * SVG_SIZE,
      svgY: ((e.clientY - rect.top) / rect.height) * SVG_SIZE,
    };
  }, []);

  const inBounds = useCallback((svgX, svgY) => {
    return svgX >= PAD && svgX <= SVG_SIZE - PAD && svgY >= PAD && svgY <= SVG_SIZE - PAD;
  }, []);

  // ── Mouse handlers ──

  const handleMouseMove = useCallback((e) => {
    const coords = getSvgCoords(e);
    if (!coords) return;
    const { svgX, svgY } = coords;
    const sigma = toSigma(svgX);
    const omega = toOmega(svgY);

    if (inBounds(svgX, svgY)) {
      setHover({ svgX, svgY, sigma, omega });
    } else {
      setHover(null);
    }

    // Update drag position — use functional update to avoid dragState dependency
    if (isDraggingRef.current) {
      setDragState(prev => prev ? { ...prev, currentSigma: sigma, currentOmega: omega, moved: true } : null);
    }
  }, [getSvgCoords, toSigma, toOmega, inBounds]);

  const handleMouseLeave = useCallback(() => {
    setHover(null);
    if (isDraggingRef.current) {
      setDragState(null);
      isDraggingRef.current = false;
    }
  }, []);

  // Click to add — suppressed after drag
  const handleClick = useCallback((e) => {
    if (clickSuppressed.current) {
      clickSuppressed.current = false;
      return;
    }
    if (isUpdating) return;
    const coords = getSvgCoords(e);
    if (!coords) return;
    if (!inBounds(coords.svgX, coords.svgY)) return;

    const sigma = snapValue(toSigma(coords.svgX));
    const omega = snapValue(toOmega(coords.svgY));
    onAddAtClick(sigma, omega);
  }, [isUpdating, getSvgCoords, inBounds, snapValue, toSigma, toOmega, onAddAtClick]);

  // Drag start — index is the backend index (from metadata)
  const handleMarkerMouseDown = useCallback((e, type, backendIndex) => {
    e.stopPropagation();
    e.preventDefault();
    const items = type === 'pole' ? (poles || []) : (zeros || []);
    const found = items.find(p => (p.index ?? 0) === backendIndex);
    if (!found) return;
    isDraggingRef.current = true;
    setDragState({ type, index: backendIndex, currentSigma: found.real, currentOmega: found.imag, moved: false });
  }, [poles, zeros]);

  // Drag end
  const handleMouseUp = useCallback(() => {
    if (dragState && dragState.moved) {
      clickSuppressed.current = true; // prevent click from firing
      const sigma = snapValue(dragState.currentSigma);
      const omega = snapValue(dragState.currentOmega);
      if (dragState.type === 'pole') {
        onMovePole(dragState.index, sigma, omega);
      } else {
        onMoveZero(dragState.index, sigma, omega);
      }
    }
    isDraggingRef.current = false;
    setDragState(null);
  }, [dragState, snapValue, onMovePole, onMoveZero]);

  // Left-click on marker to remove (when not dragging)
  const handleMarkerClick = useCallback((e, type, index) => {
    e.stopPropagation();
    // Only remove if this wasn't a drag
    if (clickSuppressed.current) {
      clickSuppressed.current = false;
      return;
    }
    if (type === 'pole') onRemovePole(index);
    else onRemoveZero(index);
  }, [onRemovePole, onRemoveZero]);

  // ── Grid ──
  const gridStep = useMemo(() => {
    const step = snapStep * 2 > range ? snapStep : snapStep * 2;
    return step;
  }, [snapStep, range]);

  const gridLines = useMemo(() => {
    const lines = [];
    for (let v = -Math.floor(range / gridStep) * gridStep; v <= range; v += gridStep) {
      if (v === 0) continue;
      lines.push(
        <line key={`gv${v}`} className="grid-line"
          x1={toSvgX(v)} y1={PAD} x2={toSvgX(v)} y2={SVG_SIZE - PAD} />
      );
      lines.push(
        <line key={`gh${v}`} className="grid-line"
          x1={PAD} y1={toSvgY(v)} x2={SVG_SIZE - PAD} y2={toSvgY(v)} />
      );
    }
    return lines;
  }, [range, gridStep, toSvgX, toSvgY]);

  const tickLabels = useMemo(() => {
    const labels = [];
    const fmt = (v) => {
      if (Math.abs(v) >= 1000) return `${(v/1000).toFixed(v % 1000 === 0 ? 0 : 1)}k`;
      return String(v);
    };
    for (let v = -Math.floor(range / gridStep) * gridStep; v <= range; v += gridStep) {
      if (v === 0) continue;
      const sx = toSvgX(v);
      const sy = toSvgY(v);
      if (sx > PAD + 15 && sx < SVG_SIZE - PAD - 15) {
        labels.push(
          <text key={`lx${v}`} className="axis-label" x={sx} y={SVG_SIZE - PAD + 16} textAnchor="middle">
            {fmt(v)}
          </text>
        );
      }
      if (sy > PAD + 15 && sy < SVG_SIZE - PAD - 15) {
        labels.push(
          <text key={`ly${v}`} className="axis-label" x={PAD - 8} y={sy + 4} textAnchor="end">
            {fmt(v)}
          </text>
        );
      }
    }
    return labels;
  }, [range, gridStep, toSvgX, toSvgY]);

  // Conjugate pair lines
  const conjugateLines = useMemo(() => {
    const lines = [];
    const draw = (items, prefix) => {
      const seen = new Set();
      items.forEach((p, i) => {
        if (seen.has(i) || Math.abs(p.imag) < 1) return;
        items.forEach((p2, j) => {
          if (j <= i || seen.has(j)) return;
          if (Math.abs(p.real - p2.real) < 1 && Math.abs(p.imag + p2.imag) < 1) {
            seen.add(i); seen.add(j);
            lines.push(
              <line key={`c${prefix}${i}-${j}`} className="conjugate-line"
                x1={toSvgX(p.real)} y1={toSvgY(p.imag)}
                x2={toSvgX(p2.real)} y2={toSvgY(p2.imag)} />
            );
          }
        });
      });
    };
    draw(poles || [], 'p');
    draw(zeros || [], 'z');
    return lines;
  }, [poles, zeros, toSvgX, toSvgY]);

  const markerSize = 11;
  const hitSize = 22;

  // Get marker position — during drag, follow cursor for the dragged marker
  const getPos = useCallback((type, backendIndex, item) => {
    if (dragState && dragState.type === type && dragState.index === backendIndex && dragState.moved) {
      return { x: toSvgX(dragState.currentSigma), y: toSvgY(dragState.currentOmega) };
    }
    return { x: toSvgX(item.real), y: toSvgY(item.imag) };
  }, [dragState, toSvgX, toSvgY]);

  const isDragging = dragState !== null;
  const cursorStyle = isDragging ? 'grabbing' : 'crosshair';

  return (
    <div className="afr-splane-container">
      {/* Info bar inside s-plane */}
      <div className="afr-splane-toolbar">
        <span className={`afr-splane-mode ${placementMode === 'pole' ? 'afr-splane-mode--pole' : 'afr-splane-mode--zero'}`}>
          {placementMode === 'pole' ? '× Placing Poles' : '○ Placing Zeros'}
        </span>
        <span className="afr-splane-hint">Click: place &middot; Click marker: remove &middot; Drag: move</span>
      </div>

      <svg
        ref={svgRef}
        className="afr-splane-svg"
        viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`}
        style={{ cursor: cursorStyle }}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onMouseUp={handleMouseUp}
        onContextMenu={(e) => e.preventDefault()}
        aria-label={`S-plane. Click to add ${placementMode}. ${(poles || []).length} poles, ${(zeros || []).length} zeros.`}
        role="img"
      >
        {/* Stable region fill */}
        <rect className="stable-region"
          x={PAD} y={PAD}
          width={toSvgX(0) - PAD} height={SVG_SIZE - 2 * PAD} />

        {gridLines}

        {/* Real axis */}
        <line className="axis-line"
          x1={PAD} y1={toSvgY(0)} x2={SVG_SIZE - PAD} y2={toSvgY(0)} />
        {/* jw axis */}
        <line className="jw-axis"
          x1={toSvgX(0)} y1={PAD} x2={toSvgX(0)} y2={SVG_SIZE - PAD} />

        <text className="axis-title" x={SVG_SIZE - PAD + 5} y={toSvgY(0) + 4} textAnchor="start">σ</text>
        <text className="axis-title" x={toSvgX(0) + 6} y={PAD - 5} textAnchor="start">jω</text>
        {tickLabels}

        {conjugateLines}

        {/* Hover crosshair (only when not dragging) */}
        {hover && !isDragging && (
          <g className="hover-crosshair" style={{ pointerEvents: 'none' }}>
            <line x1={hover.svgX} y1={PAD} x2={hover.svgX} y2={SVG_SIZE - PAD} />
            <line x1={PAD} y1={hover.svgY} x2={SVG_SIZE - PAD} y2={hover.svgY} />
          </g>
        )}

        {/* Drag crosshair */}
        {dragState && dragState.moved && (
          <g className="drag-crosshair" style={{ pointerEvents: 'none' }}>
            <line x1={toSvgX(dragState.currentSigma)} y1={PAD} x2={toSvgX(dragState.currentSigma)} y2={SVG_SIZE - PAD} />
            <line x1={PAD} y1={toSvgY(dragState.currentOmega)} x2={SVG_SIZE - PAD} y2={toSvgY(dragState.currentOmega)} />
          </g>
        )}

        {/* Zeros */}
        {(zeros || []).map((z, i) => {
          const idx = z.index ?? i;
          const pos = getPos('zero', idx, z);
          const beingDragged = dragState?.type === 'zero' && dragState?.index === idx && dragState?.moved;
          return (
            <g key={`z${i}`}
              onMouseDown={(e) => handleMarkerMouseDown(e, 'zero', idx)}
              onClick={(e) => handleMarkerClick(e, 'zero', idx)}
              style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
              className={beingDragged ? 'dragging-marker' : ''}
            >
              <circle className="hit-area" cx={pos.x} cy={pos.y} r={hitSize} />
              <circle className="zero-marker" cx={pos.x} cy={pos.y} r={markerSize} />
              <title>Zero {i + 1}: σ={z.real.toFixed(1)}, ω={z.imag.toFixed(1)}</title>
            </g>
          );
        })}

        {/* Poles */}
        {(poles || []).map((p, i) => {
          const idx = p.index ?? i;
          const pos = getPos('pole', idx, p);
          const beingDragged = dragState?.type === 'pole' && dragState?.index === idx && dragState?.moved;
          return (
            <g key={`p${i}`}
              onMouseDown={(e) => handleMarkerMouseDown(e, 'pole', idx)}
              onClick={(e) => handleMarkerClick(e, 'pole', idx)}
              style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
              className={beingDragged ? 'dragging-marker' : ''}
            >
              <circle className="hit-area" cx={pos.x} cy={pos.y} r={hitSize} />
              <line className="pole-marker"
                x1={pos.x - markerSize} y1={pos.y - markerSize}
                x2={pos.x + markerSize} y2={pos.y + markerSize} />
              <line className="pole-marker"
                x1={pos.x + markerSize} y1={pos.y - markerSize}
                x2={pos.x - markerSize} y2={pos.y + markerSize} />
              <title>Pole {i + 1}: σ={p.real.toFixed(1)}, ω={p.imag.toFixed(1)}</title>
            </g>
          );
        })}

        {/* Placement mode indicator */}
        <text x={PAD + 6} y={SVG_SIZE - PAD - 8} className="placement-hint">
          {placementMode === 'pole' ? '× Place Pole' : '○ Place Zero'}
        </text>
      </svg>

      {/* Readout bar */}
      <div className="afr-splane-readout">
        {hover ? (
          <>
            <span>σ = <strong>{snapValue(hover.sigma).toFixed(1)}</strong></span>
            <span>ω = <strong>{snapValue(hover.omega).toFixed(1)}</strong> rad/s</span>
          </>
        ) : (
          <span className="afr-splane-readout__hint">Hover for coordinates</span>
        )}
        {dragState?.moved && (
          <span className="afr-splane-readout__drag">
            Moving {dragState.type} → σ={snapValue(dragState.currentSigma).toFixed(1)}, ω={snapValue(dragState.currentOmega).toFixed(1)}
          </span>
        )}
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
  const [activePreset, setActivePreset] = useState(null);

  // Clear active preset when poles/zeros change from manual edit
  const pzFingerprint = `${poles.length}-${zeros.length}`;
  const lastPresetFP = useRef(pzFingerprint);
  useEffect(() => {
    // If fingerprint changed and we didn't just load a preset, clear active
    if (pzFingerprint !== lastPresetFP.current && activePreset) {
      // Don't clear immediately after preset load — wait for next manual change
      const timer = setTimeout(() => {
        lastPresetFP.current = pzFingerprint;
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [pzFingerprint, activePreset]);

  // ── Action handlers ──

  const handleAddAtClick = useCallback((real, imag) => {
    if (isUpdating) return;
    setActivePreset(null);
    onButtonClick('add_at_click', { real, imag, placement_mode: placementMode });
  }, [onButtonClick, isUpdating, placementMode]);

  const handleRemovePole = useCallback((index) => {
    if (isUpdating) return;
    setActivePreset(null);
    onButtonClick('remove_pole', { index });
  }, [onButtonClick, isUpdating]);

  const handleRemoveZero = useCallback((index) => {
    if (isUpdating) return;
    setActivePreset(null);
    onButtonClick('remove_zero', { index });
  }, [onButtonClick, isUpdating]);

  const handleMovePole = useCallback((index, real, imag) => {
    if (isUpdating) return;
    setActivePreset(null);
    onButtonClick('move_pole', { index, real, imag });
  }, [onButtonClick, isUpdating]);

  const handleMoveZero = useCallback((index, real, imag) => {
    if (isUpdating) return;
    setActivePreset(null);
    onButtonClick('move_zero', { index, real, imag });
  }, [onButtonClick, isUpdating]);

  const handleClearAll = useCallback(() => {
    if (isUpdating) return;
    setActivePreset(null);
    onButtonClick('clear_all', {});
  }, [onButtonClick, isUpdating]);

  const handleLoadPreset = useCallback((preset) => {
    if (isUpdating) return;
    setActivePreset(preset);
    lastPresetFP.current = 'pending'; // will be updated when state returns
    onButtonClick('load_preset', { preset });
  }, [onButtonClick, isUpdating]);

  const handleParseTf = useCallback(() => {
    if (isUpdating || !tfInput.trim()) return;
    setTfError('');
    setActivePreset(null);
    onButtonClick('parse_tf', { tf_string: tfInput.trim() });
  }, [onButtonClick, isUpdating, tfInput]);

  const handleTfKeyDown = useCallback((e) => {
    if (e.key === 'Enter') handleParseTf();
  }, [handleParseTf]);

  // Watch for backend errors related to TF parsing
  useEffect(() => {
    if (errorMsg && (errorMsg.toLowerCase().includes('parse') || errorMsg.toLowerCase().includes('expression'))) {
      setTfError(errorMsg);
    }
  }, [errorMsg]);

  // ── Plots ──
  const magPlot = useMemo(() => plots?.find(p => p.id === 'magnitude_response'), [plots]);
  const phasePlot = useMemo(() => plots?.find(p => p.id === 'phase_response'), [plots]);
  const timePlot = useMemo(() => plots?.find(p => p.id === 'time_domain'), [plots]);
  const spectrumPlot = useMemo(() => plots?.find(p => p.id === 'spectrum'), [plots]);

  // ── Badges ──
  const stabilityBadge = useMemo(() => {
    if (poles.length === 0) return null;
    if (!isStable) return <span className="afr-badge afr-badge--unstable">Unstable</span>;
    if (hasMarginal) return <span className="afr-badge afr-badge--marginal">Marginal</span>;
    return <span className="afr-badge afr-badge--stable">Stable</span>;
  }, [poles.length, isStable, hasMarginal]);

  const filterBadge = useMemo(() => {
    if (filterType === 'flat' || filterType === 'custom') return null;
    return <span className="afr-badge afr-badge--filter">{filterType}</span>;
  }, [filterType]);

  return (
    <div className="afr-viewer">
      {/* TF banner */}
      <div className="afr-tf-banner">
        <span className="afr-tf-expression">{tfExpression}</span>
        <div className="afr-tf-badges">
          {stabilityBadge}
          {filterBadge}
          <span className="afr-tf-info">
            {metadata?.system_order ?? 0}th order &middot; {poles.length}P {zeros.length}Z &middot; K={metadata?.gain_K ?? 1}
          </span>
        </div>
      </div>

      {/* Error */}
      {errorMsg && <div className="afr-error" role="alert">{errorMsg}</div>}

      {/* Split layout */}
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

      {/* Controls row: mode toggle + clear + TF input */}
      <div className="afr-controls-row">
        <div className="afr-toolbar__group">
          <button
            className={`afr-toolbar__btn ${placementMode === 'pole' ? 'afr-toolbar__btn--active-pole' : ''}`}
            onClick={() => setPlacementMode('pole')}
          >
            × Pole
          </button>
          <button
            className={`afr-toolbar__btn ${placementMode === 'zero' ? 'afr-toolbar__btn--active-zero' : ''}`}
            onClick={() => setPlacementMode('zero')}
          >
            ○ Zero
          </button>
          <button
            className="afr-toolbar__btn afr-toolbar__btn--danger"
            onClick={handleClearAll}
            disabled={isUpdating || (poles.length === 0 && zeros.length === 0)}
          >
            Clear All
          </button>
        </div>

        <div className="afr-tf-input-group">
          <label className="afr-tf-input-label">H(s) =</label>
          <input
            type="text"
            className="afr-tf-input"
            placeholder="(s+2)/(s^2+3s+1)"
            value={tfInput}
            onChange={(e) => { setTfInput(e.target.value); setTfError(''); }}
            onKeyDown={handleTfKeyDown}
            disabled={isUpdating}
          />
          <button
            className="afr-tf-input-btn"
            onClick={handleParseTf}
            disabled={isUpdating || !tfInput.trim()}
          >
            Apply
          </button>
        </div>
      </div>
      {tfError && <div className="afr-tf-input-error">{tfError}</div>}

      {/* Preset cards */}
      <div className="afr-presets-row">
        {presets.map(preset => (
          <button key={preset}
            className={`afr-preset-card ${activePreset === preset ? 'afr-preset-card--active' : ''}`}
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

      {/* Collapsible time domain + spectrum */}
      <div className={`afr-collapsible ${showTimeDomain ? 'afr-collapsible--open' : ''}`}>
        <button className="afr-collapsible__header" onClick={() => setShowTimeDomain(v => !v)} type="button">
          <span className="afr-collapsible__arrow">▸</span>
          <span>Time Domain &amp; Spectrum</span>
        </button>
        {showTimeDomain && (
          <div className="afr-collapsible__body">
            <div className="afr-plots-grid">
              {timePlot && <PlotDisplay plots={[timePlot]} />}
              {spectrumPlot && <PlotDisplay plots={[spectrumPlot]} />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AudioFreqResponseViewer;
