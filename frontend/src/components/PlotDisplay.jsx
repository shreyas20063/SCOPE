/**
 * PlotDisplay Component
 *
 * Renders Plotly charts from plot data provided by the backend.
 * Supports multiple plots, responsive sizing, and interactivity.
 * Includes theme-aware styling for dark/light modes.
 */

import React, { useMemo, memo, useEffect, useState, useRef, useCallback } from 'react';
import Plot from 'react-plotly.js';
import '../styles/PlotDisplay.css';

/* Title fitting: the modebar is always visible in the card's top-right corner,
   so long titles are nudged left, shrunk, wrapped, or moved below it. */
const TITLE_FONT_SIZE = 16;
const TITLE_GAP = 12;               // px kept clear of the card edge and the modebar
const TITLE_LINE_SPACING = 1.3;     // Plotly's line height for multi-line text
const MODEBAR_ROW_HEIGHT = 30;      // the modebar occupies the top ~30px
const MODEBAR_WIDTH_ESTIMATE = 190; // 2D cartesian modebar; replaced by the measured width
const TITLE_FONT_FAMILY = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
const TITLE_SEPARATOR = /(\s+[|—–·]\s+)/;
// Canvas measurement may run before the Inter web font has loaded (fallback
// fonts are a little narrower), so leave some slack
const TITLE_MEASURE_SLACK = 1.05;

let measureContext = null;

/**
 * Rendered width of one line of (Plotly pseudo-HTML) title text
 */
function measureTitleLine(line, size) {
  const text = line
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
  if (!measureContext && typeof document !== 'undefined') {
    measureContext = document.createElement('canvas').getContext('2d');
  }
  if (!measureContext) return text.length * size * 0.6;
  measureContext.font = `${size}px ${TITLE_FONT_FAMILY}`;
  return measureContext.measureText(text).width * TITLE_MEASURE_SLACK;
}

function widestLine(lines, size) {
  return Math.max(...lines.map((line) => measureTitleLine(line, size)));
}

/**
 * Break a title into lines no wider than maxWidth: prefer breaking at
 * separators (" | ", " — "), then between words.
 */
function wrapTitle(text, size, maxWidth) {
  const lines = [];
  text.split(/<br\s*\/?>/i).forEach((rawLine) => {
    const parts = rawLine.split(TITLE_SEPARATOR);
    const segments = [];
    let current = parts[0];
    for (let i = 1; i < parts.length; i += 2) {
      const joined = current + parts[i] + parts[i + 1];
      if (measureTitleLine(joined, size) <= maxWidth) {
        current = joined;
      } else {
        segments.push(current);
        current = parts[i + 1];
      }
    }
    segments.push(current);
    segments.forEach((segment) => {
      let line = '';
      segment.split(' ').forEach((word) => {
        const next = line ? `${line} ${word}` : word;
        if (line && measureTitleLine(next, size) > maxWidth) {
          lines.push(line);
          line = word;
        } else {
          line = next;
        }
      });
      lines.push(line);
    });
  });
  return lines;
}

/**
 * Lay the title out so it is neither clipped by the card nor covered by the
 * modebar. Returns the title text/size, its horizontal center (container
 * fraction), the px offset of the text block's top and its height (top null =
 * Plotly's default placement) and the top margin it needs (null = keep the
 * layout's own margin).
 */
function fitTitle(text, cardWidth, modebarWidth, baseMarginTop) {
  const fallback = { text, size: TITLE_FONT_SIZE, x: 0.5, top: null, height: 0, marginTop: null };
  if (!cardWidth) return fallback;

  // Tags with attributes (<span style="...">) would break if split on spaces
  const canWrap = !/<[a-z]+\s/i.test(text);
  const besideWidth = cardWidth - modebarWidth - 2 * TITLE_GAP;
  // As centered as possible while staying clear of the modebar
  const nudgedCenter = (lineWidth) => {
    const maxCenter = cardWidth - modebarWidth - TITLE_GAP - lineWidth / 2;
    const center = Math.max(TITLE_GAP + lineWidth / 2, Math.min(cardWidth / 2, maxCenter));
    return center / cardWidth;
  };
  const textHeight = (lineCount, size) => lineCount * size * TITLE_LINE_SPACING;
  // Multi-line block vertically centered in a top margin tall enough for it
  const besideModebar = (lines, size) => {
    const height = textHeight(lines.length, size);
    const marginTop = Math.max(baseMarginTop, height + 2 * TITLE_GAP);
    return {
      text: lines.join('<br>'),
      size,
      x: nudgedCenter(widestLine(lines, size)),
      top: (marginTop - height) / 2,
      height,
      marginTop,
    };
  };

  // 1) The title as given beside the modebar, shrinking the font slightly if needed
  const ownLines = text.split(/<br\s*\/?>/i);
  for (const size of [16, 15, 14]) {
    const width = widestLine(ownLines, size);
    if (width <= besideWidth) {
      if (ownLines.length > 1) return besideModebar(ownLines, size);
      return { text, size, x: nudgedCenter(width), top: null, height: 0, marginTop: null };
    }
  }

  // 2) Two lines beside the modebar
  if (canWrap && besideWidth > 0) {
    const size = 14;
    const lines = wrapTitle(text, size, besideWidth);
    if (lines.length <= 2 && widestLine(lines, size) <= besideWidth) {
      return besideModebar(lines, size);
    }
  }

  // 3) Below the modebar row, using the full card width (phones):
  //    prefer one line (down to 12px), then two lines
  const fullWidth = cardWidth - 2 * TITLE_GAP;
  let best = null;
  for (const maxLines of [1, 2]) {
    for (const size of [14, 13, 12]) {
      const lines = canWrap ? wrapTitle(text, size, fullWidth) : ownLines;
      best = { lines, size };
      if (lines.length <= maxLines && widestLine(lines, size) <= fullWidth) break;
    }
    if (best.lines.length <= maxLines && widestLine(best.lines, best.size) <= fullWidth) break;
  }
  return {
    text: best.lines.join('<br>'),
    size: best.size,
    x: 0.5,
    top: MODEBAR_ROW_HEIGHT,
    height: textHeight(best.lines.length, best.size),
    marginTop: Math.max(
      baseMarginTop,
      MODEBAR_ROW_HEIGHT + textHeight(best.lines.length, best.size) + 8
    ),
  };
}

/**
 * PNG download name for a plot, e.g. "rc_lowpass_filter_bode_magnitude"
 */
function imageFilename(plotId, index) {
  const match = typeof window !== 'undefined'
    && window.location.pathname.match(/\/simulation\/([^/?#]+)/);
  const name = [match && match[1], plotId || `plot_${index + 1}`].filter(Boolean).join('_');
  return name.replace(/[^\w.-]+/g, '_');
}

/**
 * Trace uid derived from its legend name. Plotly builds CSS selectors from
 * uids (e.g. ".cb" + uid), so it must be a plain identifier: hash the name.
 */
function traceUid(name, occurrence) {
  let hash = 5381;
  const text = String(name);
  for (let i = 0; i < text.length; i += 1) {
    hash = ((hash * 33) ^ text.charCodeAt(i)) >>> 0;
  }
  return `t${hash.toString(36)}_${occurrence}`;
}

/**
 * Deep copy of plain objects/arrays (JSON-like layout data)
 */
function clonePlain(value) {
  if (Array.isArray(value)) return value.map(clonePlain);
  if (value && typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype) {
    const copy = {};
    Object.keys(value).forEach((key) => {
      copy[key] = clonePlain(value[key]);
    });
    return copy;
  }
  return value;
}

/**
 * Backend axis has an explicit [min, max] range
 */
function hasExplicitRange(axis) {
  return Array.isArray(axis?.range) && axis.range.length === 2;
}

/**
 * The view "Reset axes" should return to for each cartesian axis of a layout:
 * a fixed [min, max] or autorange (null)
 */
function getResetTargets(layout) {
  const targets = {};
  Object.keys(layout).forEach((key) => {
    const axis = layout[key];
    if (!/^[xy]axis\d*$/.test(key) || !axis) return;
    if (axis.autorange === false && hasExplicitRange(axis)) {
      targets[key] = [axis.range[0], axis.range[1]];
    } else if (axis.autorange === true) {
      targets[key] = null;
    }
  });
  return targets;
}

/**
 * Point Plotly's "Reset axes" / double-click at the ranges the backend sent
 * most recently. Plotly only records them on the first draw, so after a
 * parameter change it would reset to the page-load view instead.
 */
function syncResetRanges(gd, targets) {
  const fullLayout = gd && gd._fullLayout;
  if (!fullLayout) return;
  Object.keys(targets).forEach((key) => {
    const fullAxis = fullLayout[key];
    if (!fullAxis) return;
    const range = targets[key];
    // Both undefined makes reset autorange to the current data
    fullAxis._rangeInitial0 = range ? range[0] : undefined;
    fullAxis._rangeInitial1 = range ? range[1] : undefined;
  });
}

/**
 * Get current theme
 */
function useTheme() {
  const [theme, setTheme] = useState(() => {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  });

  useEffect(() => {
    const observer = new MutationObserver(() => {
      const newTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      setTheme(newTheme);
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });

    return () => observer.disconnect();
  }, []);

  return theme;
}

/**
 * Theme-aware Plotly layout
 */
function getDefaultLayout(theme) {
  const isDark = theme === 'dark';

  return {
    paper_bgcolor: isDark ? '#0f172a' : '#f3f6fb',
    plot_bgcolor: isDark ? '#1e293b' : '#eaf0f8',
    font: {
      color: isDark ? '#e2e8f0' : '#1e293b',
      family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      size: 12,
    },
    xaxis: {
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      titlefont: { color: isDark ? '#cbd5e1' : '#334155', size: 12 },
      autorange: false,
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    yaxis: {
      gridcolor: isDark ? 'rgba(71, 85, 105, 0.4)' : 'rgba(100, 116, 139, 0.2)',
      gridwidth: 1,
      zerolinecolor: isDark ? 'rgba(148, 163, 184, 0.5)' : 'rgba(100, 116, 139, 0.5)',
      zerolinewidth: 1.5,
      tickfont: { color: isDark ? '#94a3b8' : '#475569', size: 11 },
      titlefont: { color: isDark ? '#cbd5e1' : '#334155', size: 12 },
      autorange: false,
      showline: true,
      linecolor: isDark ? '#475569' : '#cbd5e1',
      linewidth: 1,
    },
    margin: { t: 40, r: 25, b: 50, l: 55 },
    height: 300,  /* Explicit height to constrain Plotly chart */
    autosize: true,
    showlegend: true,
    legend: {
      font: { color: isDark ? '#e2e8f0' : '#1e293b', size: 11 },
      bgcolor: isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.95)',
      bordercolor: isDark ? '#334155' : '#e2e8f0',
      borderwidth: 1,
      orientation: 'h',
      yanchor: 'top',
      y: -0.12,
      xanchor: 'center',
      x: 0.5,
    },
    hoverlabel: {
      bgcolor: isDark ? '#1e293b' : '#ffffff',
      bordercolor: isDark ? '#475569' : '#e2e8f0',
      font: { color: isDark ? '#f1f5f9' : '#1e293b', size: 12 },
    },
  };
}

/**
 * Plotly config options
 */
const plotConfig = {
  // Resizing is driven by PlotCard's ResizeObserver instead: Plotly's own
  // resize (responsive / react-plotly's useResizeHandler) deletes
  // layout.height from the layout object it was given, so the graph would
  // grow to its container's height, and it cannot resize hidden graphs.
  responsive: false,
  displayModeBar: true,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],  // Remove autoScale to keep fixed axes
  displaylogo: false,
  toImageButtonOptions: {
    format: 'png',
    filename: 'simulation_plot',
    height: 600,
    width: 800,
    scale: 2,
  },
};

/**
 * Text Panel component for displaying theory/learning content
 */
const TextPanel = memo(function TextPanel({ plot }) {
  const theme = useTheme();
  const isDark = theme === 'dark';
  const content = plot.content || {};

  return (
    <div className="plot-card text-panel-card">
      <div className="text-panel-header">
        <h3>{plot.title || 'Information Panel'}</h3>
      </div>
      <div
        className="text-panel-content"
        style={{
          backgroundColor: isDark
            ? 'rgba(30, 41, 59, 0.8)'
            : (content.backgroundColor || 'rgba(255, 255, 255, 0.95)'),
          borderColor: content.borderColor || (isDark ? '#475569' : '#e2e8f0'),
        }}
      >
        {/* Guided scenario message if present */}
        {content.guidedMessage && (
          <div className="guided-message" style={{
            backgroundColor: isDark ? 'rgba(251, 191, 36, 0.2)' : 'rgba(251, 191, 36, 0.3)',
            borderLeft: '4px solid #f59e0b',
            padding: '12px',
            marginBottom: '16px',
            borderRadius: '4px',
          }}>
            <strong>Guided Mode:</strong> {content.guidedMessage}
          </div>
        )}

        {/* Main explanation content */}
        {content.explanation && (
          <div
            className="explanation-text"
            dangerouslySetInnerHTML={{ __html: content.explanation }}
            style={{
              fontFamily: 'monospace',
              fontSize: '13px',
              lineHeight: '1.6',
              color: isDark ? '#e2e8f0' : '#1e293b',
            }}
          />
        )}

        {/* Current status display */}
        {content.currentStatus && (
          <div className="status-display" style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: content.currentStatus.is_stable
              ? (isDark ? 'rgba(39, 174, 96, 0.2)' : 'rgba(39, 174, 96, 0.1)')
              : (isDark ? 'rgba(231, 76, 60, 0.2)' : 'rgba(231, 76, 60, 0.1)'),
            borderRadius: '6px',
            border: `1px solid ${content.currentStatus.is_stable ? '#27ae60' : '#e74c3c'}`,
          }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: content.currentStatus.is_stable ? '#27ae60' : '#e74c3c',
              marginBottom: '8px',
            }}>
              {content.currentStatus.is_stable ? '✓ STABLE' : '✗ UNSTABLE'}
            </div>
            <div style={{ fontSize: '12px', color: isDark ? '#94a3b8' : '#64748b' }}>
              <div>T/τ: {content.currentStatus.t_tau_ratio?.toFixed(3)}</div>
              <div>|z|: {content.currentStatus.z_magnitude?.toFixed(3)}</div>
              <div>RMS Error: {content.currentStatus.rms_error?.toFixed(4)}</div>
              <div>Quality: {content.currentStatus.performance_rating}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

/**
 * Single plot card component
 * Note: Not using React.memo to ensure dynamic title/label updates work correctly
 */
function PlotCard({ plot, index }) {
  const theme = useTheme();
  const defaultLayout = useMemo(() => getDefaultLayout(theme), [theme]);
  const wrapperRef = useRef(null);
  const resetTargetsRef = useRef({});
  const revisionRef = useRef({ data: undefined, signature: undefined, count: 0 });
  const [cardWidth, setCardWidth] = useState(null);
  const [modebarWidth, setModebarWidth] = useState(MODEBAR_WIDTH_ESTIMATE);
  const [fontsReady, setFontsReady] = useState(
    () => typeof document === 'undefined' || !document.fonts || document.fonts.status === 'loaded'
  );

  // Re-fit titles once web fonts have loaded (measurement depends on them)
  useEffect(() => {
    if (fontsReady) return undefined;
    let active = true;
    document.fonts.ready.then(() => {
      if (active) setFontsReady(true);
    });
    return () => {
      active = false;
    };
  }, [fontsReady]);

  // Extract values for explicit dependency tracking
  const isTextPanel = !!plot.isTextPanel;
  const plotTitle = plot.title;
  const plotData = plot.data;
  const plotId = plot.id;

  // Track the card width. Besides title fitting, this is what resizes the
  // graph: a width change rebuilds the layout and Plotly.react re-measures
  // its container. It also fires when a card that was display:none (mobile
  // tab switch, rotation while hidden) is shown again.
  useEffect(() => {
    const el = wrapperRef.current;
    if (!el || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver((entries) => {
      const width = Math.round(entries[0].contentRect.width);
      if (width > 0) setCardWidth((prev) => (prev === width ? prev : width));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [isTextPanel]);

  // Process plot data (add default styling)
  const styledData = useMemo(() => {
    if (!plotData) return [];

    // Stable per-trace uid (name + occurrence) so Plotly's uirevision keeps
    // legend show/hide choices across updates even when traces are rebuilt
    // or reordered. Unnamed traces keep Plotly's index-based matching.
    const nameCounts = {};
    return plotData.map((trace, i) => {
      let uid = trace.uid;
      if (uid === undefined && trace.name) {
        const occurrence = nameCounts[trace.name] || 0;
        nameCounts[trace.name] = occurrence + 1;
        uid = traceUid(trace.name, occurrence);
      }
      return {
        ...trace,
        ...(uid !== undefined ? { uid } : {}),
        // Add default line colors if not specified
        line: {
          width: 2,
          ...trace.line,
          color: trace.line?.color || getDefaultColor(i),
        },
        marker: {
          ...trace.marker,
          color: trace.marker?.color || getDefaultColor(i),
        },
      };
    });
  }, [plotData]);

  const config = useMemo(() => ({
    ...plotConfig,
    toImageButtonOptions: {
      ...plotConfig.toImageButtonOptions,
      filename: imageFilename(plotId, index),
    },
  }), [plotId, index]);

  const titleText = plotTitle || `Plot ${index + 1}`;
  const baseMarginTop = plot.layout?.margin?.t ?? defaultLayout.margin.t;
  const titleFit = useMemo(
    () => fitTitle(titleText, cardWidth, modebarWidth, baseMarginTop),
    // fontsReady: re-measure with the real font
    [titleText, cardWidth, modebarWidth, baseMarginTop, fontsReady]
  );

  // After each Plotly render: measure the real modebar width (it differs by
  // plot type) and keep "Reset axes" pointed at the latest backend ranges.
  const handleRendered = useCallback((figure, gd) => {
    const modebar = gd && gd.querySelector && gd.querySelector('.modebar');
    const width = modebar ? Math.round(modebar.getBoundingClientRect().width) : 0;
    if (width > 0) {
      setModebarWidth((prev) => (Math.abs(prev - width) > 2 ? width : prev));
    }
    syncResetRanges(gd, resetTargetsRef.current);
  }, []);

  // Revision counter (datarevision + react-plotly's numeric `revision`).
  // With datarevision set, Plotly.react treats unchanged datarevision as
  // "data arrays unchanged", so bump it whenever the backend sends new data
  // (new array identity) or the sampled signature changes (in-place edits).
  const computeSignature = () => {
    const traceInfo = plotData?.map((trace, i) => {
      const len = trace.y?.length || 0;
      // Sample multiple points for better change detection
      const y0 = trace.y?.[0];
      const yMid = trace.y?.[Math.floor(len / 2)];
      const yQuarter = trace.y?.[Math.floor(len / 4)];
      const x0 = trace.x?.[0];
      const xLast = trace.x?.[len - 1];

      const fmt = (v) => typeof v === 'number' ? v.toFixed(4) : (v ?? 'na');
      return `${i}:${trace.name || ''}:${len}:${fmt(x0)}:${fmt(xLast)}:${fmt(y0)}:${fmt(yQuarter)}:${fmt(yMid)}`;
    }).join('|') || 'empty';
    return `${plotId}-${plotTitle}-${traceInfo}`;
  };
  const signature = computeSignature();
  if (revisionRef.current.data !== plotData || revisionRef.current.signature !== signature) {
    revisionRef.current = {
      data: plotData,
      signature,
      count: revisionRef.current.count + 1,
    };
  }
  const revision = revisionRef.current.count;

  // Merge default layout with plot-specific layout. Memoized on the plot
  // object (new for every backend update) so unrelated re-renders don't call
  // Plotly.react again: Plotly.react writes uirevision-restored GUI state
  // (zoom ranges, legend-hidden traces) into the layout/traces it is given,
  // and a repeat call with those same objects reads them back as new input,
  // dropping the user's zoom / hidden traces on the next update.
  const isDark = theme === 'dark';
  const { layout, data, resetTargets } = useMemo(() => {
    // Own copy of the backend layout so those GUI writes never reach plot state
    const plotLayout = clonePlain(plot.layout || {});
    const layout = {
      ...defaultLayout,
      ...plotLayout,
      // Theme-aware colors MUST override backend hardcodes
      paper_bgcolor: defaultLayout.paper_bgcolor,
      plot_bgcolor: defaultLayout.plot_bgcolor,
      // Title: Use plot.title directly (dynamic from backend), fitted to the
      // card width so it is never clipped or hidden under the modebar
      title: {
        text: titleFit.text,
        font: { color: isDark ? '#f1f5f9' : '#1e293b', size: titleFit.size },
        x: titleFit.x,
        xanchor: 'center',
        // Plotly centers multi-line titles on their anchor whatever the
        // yanchor, so place the block by its middle
        ...(titleFit.top !== null
          ? {
            yref: 'container',
            yanchor: 'middle',
            y: 1 - (titleFit.top + titleFit.height / 2)
              / (plotLayout.height || defaultLayout.height),
          }
          : {}),
      },
      ...(titleFit.marginTop !== null
        ? { margin: { ...defaultLayout.margin, ...plotLayout.margin, t: titleFit.marginTop } }
        : {}),
      xaxis: {
        ...defaultLayout.xaxis,
        ...plotLayout.xaxis,
        // Fixed axes only where the backend gave a range; otherwise fit the data
        // (autorange:false with no range would show Plotly's default [-1, 6]).
        autorange: plotLayout.xaxis?.autorange !== undefined
          ? plotLayout.xaxis.autorange
          : !hasExplicitRange(plotLayout.xaxis),
        fixedrange: false,
        title: {
          text: plotLayout.xaxis?.title || '',
          font: { color: isDark ? '#94a3b8' : '#334155' },
        },
      },
      yaxis: {
        ...defaultLayout.yaxis,
        ...plotLayout.yaxis,
        autorange: plotLayout.yaxis?.autorange !== undefined
          ? plotLayout.yaxis.autorange
          : !hasExplicitRange(plotLayout.yaxis),
        fixedrange: false,
        title: {
          text: plotLayout.yaxis?.title || '',
          font: { color: isDark ? '#94a3b8' : '#334155' },
        },
      },
      // Merge legend with theme-aware defaults
      legend: {
        ...defaultLayout.legend,
        ...plotLayout.legend,
        font: {
          ...defaultLayout.legend?.font,
          ...plotLayout.legend?.font,
          color: isDark ? '#e2e8f0' : '#1e293b',
        },
        bgcolor: isDark ? 'rgba(30, 41, 59, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      },
      // Explicitly pass shapes and annotations from backend
      shapes: plotLayout.shapes || [],
      annotations: plotLayout.annotations || [],
      // datarevision changes when the data changes, triggering a Plotly data update
      datarevision: revision,
      // uirevision: use backend value if provided, otherwise plotId for zoom/pan preservation
      uirevision: plotLayout.uirevision || plotId || 'stable',
    };
    // No layout.transition: whenever it is set, Plotly.react takes its
    // transition path and never redraws annotations/shapes, so they go stale.
    delete layout.transition;
    return {
      layout,
      data: styledData.map((trace) => ({ ...trace })),
      // Captured before Plotly writes GUI state into `layout`
      resetTargets: getResetTargets(layout),
    };
    // cardWidth: re-run Plotly.react (which re-measures its container) when
    // the card is resized or shown again after being display:none
  }, [plot, styledData, defaultLayout, isDark, titleFit, revision, plotId, cardWidth]);
  resetTargetsRef.current = resetTargets;

  // Handle text panels (like Theory Panel)
  if (isTextPanel) {
    return <TextPanel plot={plot} />;
  }

  return (
    <div className="plot-card">
      {plot.description && (
        <p className="plot-description">{plot.description}</p>
      )}
      <div className="plot-wrapper" ref={wrapperRef}>
        <Plot
          data={data}
          layout={layout}
          config={config}
          useResizeHandler={false}
          style={{ width: '100%', height: '100%' }}
          revision={revision}
          onInitialized={handleRendered}
          onUpdate={handleRendered}
          onError={handlePlotError}
        />
      </div>
    </div>
  );
}

/**
 * react-plotly swallows Plotly.react failures, which leaves a stale plot on
 * screen with no trace; surface them.
 */
function handlePlotError(err) {
  console.error('[PlotDisplay] Plotly render failed:', err);
}

/**
 * Get default color for trace by index
 * Modern vibrant palette optimized for dark mode
 */
function getDefaultColor(index) {
  const colors = [
    '#60a5fa', // sky blue
    '#34d399', // emerald
    '#fbbf24', // amber
    '#f87171', // coral
    '#a78bfa', // violet
    '#2dd4bf', // teal
    '#fb923c', // orange
    '#f472b6', // pink
    '#38bdf8', // light blue
    '#4ade80', // green
  ];
  return colors[index % colors.length];
}

/**
 * Loading skeleton for plots
 */
function PlotSkeleton() {
  return (
    <div className="plot-card plot-skeleton">
      <div className="skeleton-title"></div>
      <div className="skeleton-chart"></div>
    </div>
  );
}

/**
 * Main PlotDisplay component
 * Note: Not memoized to ensure dynamic updates propagate correctly
 */
function PlotDisplay({ plots = [], isLoading = false, emptyMessage = null }) {
  if (isLoading) {
    return (
      <div className="plots-container">
        <PlotSkeleton />
        <PlotSkeleton />
      </div>
    );
  }

  if (!plots || plots.length === 0) {
    return (
      <div className="plots-container">
        <div className="plots-empty">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="20" x2="18" y2="10" />
            <line x1="12" y1="20" x2="12" y2="4" />
            <line x1="6" y1="20" x2="6" y2="14" />
          </svg>
          <p>{emptyMessage || 'No plots to display. Adjust parameters to see results.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="plots-container">
      {plots.map((plot, index) => (
        <PlotCard
          key={plot.id || `plot-${index}`}
          plot={plot}
          index={index}
        />
      ))}
    </div>
  );
}

export default PlotDisplay;
