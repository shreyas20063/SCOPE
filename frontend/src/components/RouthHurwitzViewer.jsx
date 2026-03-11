/**
 * Routh-Hurwitz Stability Criterion Viewer
 *
 * Spacious, polished layout focused on the Routh array table with
 * sign-change highlighting, pole-zero map, and parametric K analysis.
 */

import React, { useMemo, useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/RouthHurwitzViewer.css';

/* ---------- Theme hook ---------- */
function useTheme() {
  const [theme, setTheme] = useState(() =>
    document.documentElement.getAttribute('data-theme') || 'dark'
  );
  useEffect(() => {
    const obs = new MutationObserver(() =>
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark')
    );
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => obs.disconnect();
  }, []);
  return theme;
}

/* ---------- KaTeX polynomial renderer ---------- */
function PolyEquation({ latex }) {
  const html = useMemo(() => {
    if (!latex) return '';
    try {
      return katex.renderToString(latex + ' = 0', { throwOnError: false, displayMode: false });
    } catch {
      return latex + ' = 0';
    }
  }, [latex]);

  return <span className="rh-poly-equation" dangerouslySetInnerHTML={{ __html: html }} />;
}

/* ---------- Routh Array Table ---------- */
function RouthTable({ routhTable }) {
  if (!routhTable || !routhTable.rows || routhTable.rows.length === 0) {
    return <div className="rh-routh-body" style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Enter a valid polynomial to see the Routh array</div>;
  }

  const { rows, powers, first_column, sign_changes, flags, stable } = routhTable;
  const flagMap = {};
  (flags || []).forEach(f => { flagMap[f.row] = f; });

  const n_cols = rows[0]?.length || 0;
  const hasFlags = flags && flags.length > 0;

  // Determine if marginal (stable but has jω poles — sign_changes === 0 but some first_col ≈ 0)
  const hasMarginal = stable && first_column.some(v => Math.abs(v) < 1e-6);

  const summaryClass = !stable ? 'unstable' : hasMarginal ? 'marginal' : 'stable';
  const summaryIcon = !stable ? '✕' : hasMarginal ? '⚠' : '✓';
  const summaryText = !stable
    ? `${sign_changes} sign change${sign_changes !== 1 ? 's' : ''} in first column → ${sign_changes} RHP pole${sign_changes !== 1 ? 's' : ''} → Unstable`
    : hasMarginal
    ? 'No sign changes — marginally stable (poles on jω axis)'
    : 'No sign changes in first column → All poles in LHP → Stable';

  return (
    <div className="rh-routh-body">
      <table className="rh-routh-table">
        <thead>
          <tr>
            <th>Power</th>
            {Array.from({ length: n_cols }, (_, j) => (
              <th key={j}>c{j + 1}</th>
            ))}
            {hasFlags && <th>Note</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const prevSign = i > 0 ? Math.sign(first_column[i - 1]) : Math.sign(first_column[0]);
            const currSign = Math.sign(first_column[i]);
            const signChange = i > 0 && prevSign !== 0 && currSign !== 0 && prevSign !== currSign;
            const flag = flagMap[i];

            return (
              <tr key={i} className={flag ? 'rh-routh-flagged' : ''}>
                <td className="rh-routh-power">{powers[i]}</td>
                {row.map((val, j) => (
                  <td
                    key={j}
                    className={`rh-routh-cell ${j === 0 && signChange ? 'sign-change' : ''}`}
                  >
                    {Math.abs(val) < 1e-10 ? '0' : formatValue(val)}
                  </td>
                ))}
                {hasFlags && (
                  <td className="rh-routh-flag-cell">
                    {flag && (
                      <span className="rh-routh-flag">
                        {flag.type === 'epsilon' ? 'ε replaced' : 'aux poly'}
                      </span>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className={`rh-routh-summary ${summaryClass}`}>
        <span className="rh-summary-icon">{summaryIcon}</span>
        <span>{summaryText}</span>
      </div>
    </div>
  );
}

/* ---------- Stability Ranges Bar ---------- */
function StabilityBar({ stabilityRanges, currentK, kMax }) {
  if (!stabilityRanges || !stabilityRanges.ranges || stabilityRanges.ranges.length === 0) {
    return null;
  }

  const { ranges, critical_k_values } = stabilityRanges;
  const totalRange = kMax || ranges[ranges.length - 1]?.end || 100;

  const kPercent = currentK != null ? (currentK / totalRange) * 100 : null;

  return (
    <div className="rh-stability-body">
      <div className="rh-stability-bar-container">
        <div className="rh-stability-bar-label">Stability Map (K = 0 to {totalRange})</div>
        <div className="rh-stability-bar" style={{ position: 'relative' }}>
          {ranges.map((r, i) => {
            const width = ((r.end - r.start) / totalRange) * 100;
            return (
              <div
                key={i}
                className={`rh-stability-segment ${r.stable ? 'stable' : 'unstable'}`}
                style={{ width: `${width}%` }}
              >
                <span className="rh-stability-segment-label">
                  {r.stable ? 'Stable' : 'Unstable'}
                </span>
              </div>
            );
          })}
          {kPercent != null && (
            <>
              <div className="rh-stability-k-indicator" style={{ left: `${kPercent}%` }}>
                <span className="rh-stability-k-label">K={currentK?.toFixed(1)}</span>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="rh-stability-ranges-list">
        {ranges.map((r, i) => (
          <span key={i} className={`rh-stability-range-tag ${r.stable ? 'stable' : 'unstable'}`}>
            {r.stable ? '✓' : '✕'} K ∈ [{r.start.toFixed(1)}, {r.end.toFixed(1)}]
          </span>
        ))}
        {critical_k_values && critical_k_values.length > 0 && (
          <span className="rh-stability-range-tag" style={{ background: 'rgba(148,163,184,0.08)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
            Critical K: {critical_k_values.map(k => k.toFixed(2)).join(', ')}
          </span>
        )}
      </div>
    </div>
  );
}

/* ---------- Roots Info Chips ---------- */
function RootsInfo({ roots }) {
  if (!roots || roots.length === 0) return null;

  return (
    <div className="rh-roots-info">
      {roots.map((r, i) => {
        const cls = r.marginal ? 'marginal' : r.stable ? 'stable' : 'unstable';
        const im = r.im;
        let label = `${r.re.toFixed(3)}`;
        if (Math.abs(im) > 1e-6) {
          label += ` ${im >= 0 ? '+' : '−'} ${Math.abs(im).toFixed(3)}j`;
        }
        return <span key={i} className={`rh-root-chip ${cls}`}>{label}</span>;
      })}
    </div>
  );
}

/* ---------- Helpers ---------- */
function formatValue(val) {
  if (Number.isInteger(val) || Math.abs(val - Math.round(val)) < 1e-8) {
    return Math.round(val).toString();
  }
  if (Math.abs(val) >= 1000 || (Math.abs(val) < 0.01 && Math.abs(val) > 1e-12)) {
    return val.toExponential(3);
  }
  return val.toFixed(3);
}

/* ---------- Main Viewer ---------- */
function RouthHurwitzViewer({ metadata, plots }) {
  const theme = useTheme();
  const isDark = theme === 'dark';

  if (!metadata) {
    return <div className="rh-viewer" style={{ padding: '40px', color: 'var(--text-muted)', textAlign: 'center' }}>Loading simulation...</div>;
  }

  const {
    polynomial_latex,
    degree,
    routh_table,
    roots,
    stability_ranges,
    preset_description,
    use_parametric_k,
    current_k,
  } = metadata;

  const isStable = routh_table?.stable;
  const signChanges = routh_table?.sign_changes || 0;
  const hasMarginal = isStable && (routh_table?.first_column || []).some(v => Math.abs(v) < 1e-6);

  const stabilityClass = !isStable ? 'unstable' : hasMarginal ? 'marginal' : 'stable';
  const stabilityLabel = !isStable ? `${signChanges} RHP pole${signChanges !== 1 ? 's' : ''}` : hasMarginal ? 'Marginal' : 'Stable';

  // Find plots by id
  const poleZeroPlot = plots?.find(p => p.id === 'pole_zero_map');
  const kStabilityPlot = plots?.find(p => p.id === 'k_stability_map');

  const plotlyConfig = { responsive: true, displayModeBar: true, displaylogo: false, modeBarButtonsToRemove: ['select2d', 'lasso2d'] };

  const plotTheme = useMemo(() => ({
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255,255,255,0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: { family: 'Inter, sans-serif', size: 12, color: isDark ? '#f1f5f9' : '#1e293b' },
  }), [isDark]);

  return (
    <div className="rh-viewer">
      {/* Polynomial Banner */}
      <div className="rh-poly-banner">
        <div className="rh-poly-main">
          <span className="rh-poly-label">Characteristic Polynomial</span>
          <PolyEquation latex={polynomial_latex} />
        </div>
        <div className="rh-poly-badges">
          <span className="rh-badge rh-badge-degree">Degree {degree}</span>
          <span className={`rh-badge rh-badge-${stabilityClass}`}>{stabilityLabel}</span>
        </div>
      </div>

      {preset_description && (
        <div className="rh-preset-desc" style={{ marginTop: '-16px', paddingLeft: '4px' }}>{preset_description}</div>
      )}

      {/* Routh Array Table */}
      <div className="rh-routh-section">
        <div className="rh-section-header">
          <div>
            <span className="rh-section-title">Routh Array</span>
            <span className="rh-section-subtitle" style={{ marginLeft: '12px' }}>
              First-column sign changes = RHP poles
            </span>
          </div>
        </div>
        <RouthTable routhTable={routh_table} />
      </div>

      {/* Stability Ranges (Parametric K) */}
      {use_parametric_k && stability_ranges && stability_ranges.ranges && stability_ranges.ranges.length > 0 && (
        <div className="rh-stability-section">
          <div className="rh-section-header">
            <span className="rh-section-title">Stability Ranges</span>
            <span className="rh-section-subtitle">K added to constant coefficient</span>
          </div>
          <StabilityBar
            stabilityRanges={stability_ranges}
            currentK={current_k}
            kMax={stability_ranges.ranges[stability_ranges.ranges.length - 1]?.end}
          />
        </div>
      )}

      {/* Plots */}
      <div className={`rh-plots-row ${!kStabilityPlot ? 'single' : ''}`}>
        {/* Pole-Zero Map */}
        {poleZeroPlot && (
          <div className="rh-plot-card">
            <div className="rh-plot-header">Pole Locations (s-plane)</div>
            <div className="rh-plot-body">
              <Plot
                data={poleZeroPlot.data || []}
                layout={{
                  ...poleZeroPlot.layout,
                  ...plotTheme,
                  datarevision: `pzm-${Date.now()}`,
                  uirevision: 'pole_zero_map',
                  autosize: true,
                  height: 350,
                }}
                config={plotlyConfig}
                useResizeHandler
                style={{ width: '100%', height: '350px' }}
              />
            </div>
            <RootsInfo roots={roots} />
          </div>
        )}

        {/* K Stability Map */}
        {kStabilityPlot && (
          <div className="rh-plot-card">
            <div className="rh-plot-header">RHP Poles vs Gain K</div>
            <div className="rh-plot-body">
              <Plot
                data={kStabilityPlot.data || []}
                layout={{
                  ...kStabilityPlot.layout,
                  ...plotTheme,
                  datarevision: `ksm-${Date.now()}`,
                  uirevision: 'k_stability_map',
                  autosize: true,
                  height: 350,
                }}
                config={plotlyConfig}
                useResizeHandler
                style={{ width: '100%', height: '350px' }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RouthHurwitzViewer;
