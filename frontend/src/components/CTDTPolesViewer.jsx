/**
 * CTDTPolesViewer
 *
 * Custom viewer for the CT/DT Poles Conversion simulation.
 * Layout: guided-scenario banner, pole-conversion cards (CT pole, exact
 * e^{sT}, method pole, error, equivalent CT pole, stability, quality),
 * the difference-equation stage (KaTeX derivation + first samples table),
 * four themed Plotly plots, and the method's theory card.
 */

import React, { useEffect, useMemo, useRef, useState } from 'react';
import Plot from 'react-plotly.js';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../styles/CTDTPolesViewer.css';

function useTheme() {
  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute('data-theme') || 'dark'
  );
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark');
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);
  return theme;
}

/** Fixed-decimal number with '-0.000' normalised and the true minus sign. */
function fmt(v, d = 4) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  if (!Number.isFinite(v)) return v > 0 ? '∞' : '−∞';
  if (Math.abs(v) >= 1e6) return v.toExponential(2).replace('-', '−');
  let s = v.toFixed(d);
  if (Number(s) === 0) s = s.replace('-', '');
  return s.replace('-', '−');
}

function Tex({ tex, block = false, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current && tex) {
      try {
        katex.render(tex, ref.current, { throwOnError: false, displayMode: block });
      } catch { /* throwOnError: false renders the source in red instead */ }
    }
  }, [tex, block]);
  const Tag = block ? 'div' : 'span';
  return <Tag ref={ref} className={`ctdt-tex ${className}`} />;
}

// Darker trace colors in light mode keep lines/markers at >= 3:1 contrast.
const LIGHT_TRACE_COLORS = {
  '#3b82f6': '#1d4ed8',
  '#14b8a6': '#0f766e',
  '#f59e0b': '#b45309',
  '#ef4444': '#b91c1c',
  '#8b5cf6': '#6d28d9',
  '#10b981': '#047857',
  '#ec4899': '#be185d',
};

function hashKey(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i += 1) h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
  return h.toString(36);
}

// Always returns a fresh trace object (Plotly.react writes legend/uirevision
// state into the objects it is given) with a stable uid so legend toggles persist.
function adaptTrace(trace, isDark, uid) {
  const out = { ...trace, uid };
  if (isDark) return out;
  const map = (c) => (typeof c === 'string' && LIGHT_TRACE_COLORS[c.toLowerCase()]) || c;
  if (trace.line) out.line = { ...trace.line, color: map(trace.line.color) };
  if (trace.marker) {
    out.marker = { ...trace.marker, color: map(trace.marker.color) };
    if (trace.marker.line) out.marker.line = { ...trace.marker.line, color: map(trace.marker.line.color) };
  }
  return out;
}

function adaptAnnotation(a, isDark) {
  if (isDark || !a.font?.color) return a;
  return { ...a, font: { ...a.font, color: LIGHT_TRACE_COLORS[a.font.color.toLowerCase()] || a.font.color } };
}

const PLOT_HEIGHTS = { s_plane: 430, z_plane: 430, response: 400, pole_vs_step: 360 };

function ThemedPlot({ plot, isDark, revision }) {
  const text = isDark ? '#e2e8f0' : '#1e293b';
  const muted = isDark ? '#94a3b8' : '#475569';
  const grid = isDark ? 'rgba(148, 163, 184, 0.12)' : 'rgba(100, 116, 139, 0.18)';
  const zero = isDark ? 'rgba(148, 163, 184, 0.45)' : 'rgba(71, 85, 105, 0.45)';
  // Copy range arrays: Plotly zoom/relayout mutates them in place.
  const axis = (ax = {}) => ({
    ...ax,
    ...(Array.isArray(ax.range) ? { range: [...ax.range] } : {}),
    title:{ text: typeof ax.title === 'string' ? ax.title : ax.title?.text || '', font: { size: 12, color: muted } },
    tickfont: { size: 11, color: muted },
    gridcolor: grid,
    zerolinecolor: zero,
    linecolor: grid,
    automargin: true,
  });
  const base = plot.layout || {};
  const layout = {
    ...base,
    height: PLOT_HEIGHTS[plot.id] || 380,
    autosize: true,
    paper_bgcolor: isDark ? '#0a0e27' : 'rgba(255, 255, 255, 0.98)',
    plot_bgcolor: isDark ? '#131b2e' : '#f8fafc',
    font: { family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', size: 12, color: text },
    xaxis: axis(base.xaxis),
    yaxis: axis(base.yaxis),
    legend: { ...(base.legend || {}), bgcolor: 'rgba(0,0,0,0)', font: { size: 11, color: text } },
    annotations: (base.annotations || []).map((a) => adaptAnnotation(a, isDark)),
    hoverlabel: { font: { family: 'Inter, sans-serif', size: 12 } },
    datarevision: revision,
  };
  const data = useMemo(() => {
    const seen = {};
    return (plot.data || []).map((t) => {
      const key = t.name || 'trace';
      seen[key] = (seen[key] || 0) + 1;
      // Plotly puts the uid into CSS selectors, so it must be selector-safe.
      return adaptTrace(t, isDark, `${plot.id}-${hashKey(key)}-${seen[key]}`);
    });
  }, [plot.data, plot.id, isDark]);
  const config = useMemo(() => ({
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'toggleSpikelines'],
    toImageButtonOptions: { format: 'png', filename: `ct_dt_poles_${plot.id}`, scale: 2 },
  }), [plot.id]);
  return (
    <Plot
      data={data}
      layout={layout}
      config={config}
      revision={revision}
      onError={(err) => console.error(`[CTDTPolesViewer] Plotly failed to render ${plot.id}:`, err)}
      useResizeHandler
      style={{ width: '100%', height: `${layout.height}px` }}
    />
  );
}

const PLOT_INFO = {
  s_plane: {
    title: 's-plane',
    caption: 'CT pole sₚ (×), the region the selected method maps inside |z| < 1 (green), and the equivalent CT pole of the DT recursion, s_eq = ln(z_d)/T.',
  },
  z_plane: {
    title: 'z-plane',
    caption: 'The method pole z_d (×) next to the exact sampled pole e^(sₚT) (◇). The dashed curve is where the method sends the jω axis.',
  },
  response: {
    title: 'Step response of the difference equation',
    caption: 'DT samples y[n] (stems) start at rest, y[0] = y(0) = 0, and are drawn at t = nT on top of the exact CT step response y(t).',
  },
  pole_vs_step: {
    title: 'DT pole vs step size',
    caption: 'How z_d moves as T/τ grows, compared with the exact pole e^(−T/τ). Outside the green band the recursion diverges.',
  },
};

function PlotCard({ plot, isDark, revision }) {
  const info = PLOT_INFO[plot.id] || { title: plot.title, caption: '' };
  return (
    <section className={`ctdt-plot-card ctdt-plot-card--${plot.id}`} aria-label={info.title}>
      <header className="ctdt-plot-card__header">
        <h4 className="ctdt-plot-card__title">{info.title}</h4>
        <p className="ctdt-plot-card__caption">{info.caption}</p>
      </header>
      <ThemedPlot plot={plot} isDark={isDark} revision={revision} />
    </section>
  );
}

const STATUS_LABEL = { stable: 'STABLE', marginal: 'MARGINALLY STABLE', unstable: 'UNSTABLE' };

function PoleCards({ info }) {
  const isExact = info.method === 'exact_zoh';
  const sEq = info.s_equivalent || {};
  let sEqValue;
  if (sEq.kind === 'deadbeat') sEqValue = '→ −∞';
  else if (sEq.kind === 'pair') sEqValue = `${fmt(sEq.re)} ± j${fmt(sEq.im)}`;
  else sEqValue = fmt(sEq.re);
  const relErr = info.z_exact ? (100 * info.pole_error) / info.z_exact : null;
  const rating = info.performance_rating;
  let quality;
  if (rating === 'EXACT') {
    quality = 'Samples equal y(nT) exactly';
  } else if (info.rms_error === null || info.rms_error === undefined) {
    quality = 'No error metric: the recursion does not converge';
  } else {
    quality = `RMS error vs y(nT) over 0 ≤ t ≤ 6τ: ${fmt(info.rms_error)}`;
  }

  return (
    <div className="ctdt-cards" role="group" aria-label="Pole conversion summary">
      <div className="ctdt-card">
        <span className="ctdt-card__label">CT pole</span>
        <span className="ctdt-card__value ctdt-color-ct">s<sub>p</sub> = {fmt(info.s_pole)}</span>
        <span className="ctdt-card__sub">sₚ = −1/τ, τ = {fmt(info.tau, 2)} s</span>
      </div>
      <div className="ctdt-card ctdt-card--exact">
        <span className="ctdt-card__label">Exact DT pole (CT → DT)</span>
        <span className="ctdt-card__value ctdt-color-ct">z = {fmt(info.z_exact)}</span>
        <span className="ctdt-card__sub">z = e<sup>sₚT</sup> with T = {fmt(info.T, 2)} s</span>
      </div>
      <div className={`ctdt-card ctdt-card--${info.stability}`}>
        <span className="ctdt-card__label">{isExact ? 'Method pole (exact)' : `${info.method_name} pole`}</span>
        <span className={`ctdt-card__value ctdt-color-${info.stability}`}>z<sub>d</sub> = {fmt(info.z_method)}</span>
        <span className="ctdt-card__sub">|z<sub>d</sub>| = {fmt(info.z_magnitude)}</span>
      </div>
      <div className="ctdt-card">
        <span className="ctdt-card__label">Pole error <span className="ctdt-math">z<sub>d</sub> − e<sup>sₚT</sup></span></span>
        <span className="ctdt-card__value">{fmt(info.pole_error)}</span>
        <span className="ctdt-card__sub">{relErr === null ? '—' : `${fmt(relErr, 1)}% of the exact pole`}</span>
      </div>
      <div className="ctdt-card">
        <span className="ctdt-card__label">Equivalent CT pole (DT → CT)</span>
        <span className={`ctdt-card__value ctdt-color-${info.stability}`}>s<sub>eq</sub> = {sEqValue}</span>
        <span className="ctdt-card__sub">s<sub>eq</sub> = ln(z<sub>d</sub>)/T vs sₚ = {fmt(info.s_pole)}</span>
      </div>
      <div className={`ctdt-card ctdt-card--${info.stability}`}>
        <span className="ctdt-card__label">DT stability</span>
        <span className={`ctdt-card__value ctdt-color-${info.stability}`}>{STATUS_LABEL[info.stability]}</span>
        <span className="ctdt-card__sub">{info.mode_behavior}</span>
      </div>
      <div className="ctdt-card">
        <span className="ctdt-card__label">Approximation quality</span>
        <span className={`ctdt-card__value ctdt-rating ctdt-rating--${(rating || '').toLowerCase()}`}>{rating}</span>
        <span className="ctdt-card__sub">{quality}</span>
      </div>
    </div>
  );
}

function SamplesTable({ samples, info }) {
  if (!samples?.length) return null;
  const cell = (v) => (Number.isFinite(v) ? fmt(v) : 'overflow');
  return (
    <div className="ctdt-table-wrap">
      <table className="ctdt-table">
        <caption>First samples of the step response; both start at rest, y[0] = y(0) = 0.</caption>
        <thead>
          <tr>
            <th scope="col">n</th>
            <th scope="col">t = nT</th>
            <th scope="col">y[n] (DT)</th>
            <th scope="col">y(nT) (CT)</th>
            <th scope="col">error</th>
          </tr>
        </thead>
        <tbody>
          {samples.map((s) => (
            <tr key={s.n} className={s.n === 0 ? 'ctdt-table__ic' : ''}>
              <td>{s.n}</td>
              <td>{fmt(s.t, 2)}</td>
              <td className={`ctdt-color-${info.stability}`}>{cell(s.y_dt)}</td>
              <td className="ctdt-color-ct">{cell(s.y_ct)}</td>
              <td>{cell(s.error)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DifferenceEquationStage({ eq, info, samples }) {
  if (!eq) return null;
  const isExact = info.method === 'exact_zoh';
  return (
    <section className="ctdt-panel" aria-label="Difference-equation stage">
      <h4 className="ctdt-panel__title">Difference-equation stage</h4>
      <div className="ctdt-stage">
        <ol className="ctdt-steps">
          <li>
            <span className="ctdt-step__label">CT model (initially at rest)</span>
            <Tex block tex={eq.ct_ode} />
            <Tex block tex={eq.ct_tf} />
            <Tex block tex={eq.params} className="ctdt-tex--small" />
            <Tex block tex={eq.input} className="ctdt-tex--small" />
          </li>
          <li>
            <span className="ctdt-step__label">{info.method_name}: CT → DT pole map</span>
            <Tex block tex={eq.derivative} />
            {!isExact && <Tex block tex={`\\Longleftrightarrow\\quad ${eq.substitution}`} />}
            <Tex block tex={`${eq.pole_map} \\;\\Rightarrow\\; ${eq.pole_map_num}`} />
            <Tex block tex={eq.exact_map} className="ctdt-tex--ct" />
          </li>
          <li>
            <span className="ctdt-step__label">Difference equation (starts at rest)</span>
            <Tex block tex={eq.diff_sym} />
            <Tex block tex={eq.diff_num} />
            <Tex block tex={eq.ic} />
          </li>
          <li>
            <span className="ctdt-step__label">Step response: the pole sets the decay ratio</span>
            <Tex block tex={eq.dt_sym} />
            <Tex block tex={eq.dt_closed} />
            <Tex block tex={eq.ct_closed} className="ctdt-tex--ct" />
          </li>
          <li>
            <span className="ctdt-step__label">Back to CT (DT → CT)</span>
            {!isExact && (
              <p className="ctdt-note">
                Undoing the method&apos;s own substitution (<Tex tex={eq.inverse_map} />) just returns sₚ.
                The exact inverse <Tex tex={'s = \\ln(z)/T'} /> tells you which CT pole the DT recursion really behaves like:
              </p>
            )}
            <Tex block tex={eq.inverse_num} />
          </li>
        </ol>
        <SamplesTable samples={samples} info={info} />
      </div>
    </section>
  );
}

function TheoryCard({ methodInfo, isExact }) {
  if (!methodInfo) return null;
  return (
    <section className="ctdt-panel ctdt-theory" aria-label="Method theory">
      <h4 className="ctdt-panel__title">About {methodInfo.name}</h4>
      <div className="ctdt-theory__maps">
        <div><span className="ctdt-step__label">CT → DT</span><Tex block tex={methodInfo.pole_map} /></div>
        <div><span className="ctdt-step__label">DT → CT</span><Tex block tex={methodInfo.inverse_map} /></div>
      </div>
      <dl className="ctdt-theory__list">
        <dt>Idea</dt><dd>{methodInfo.concept}</dd>
        <dt>Where the s-plane goes</dt><dd>{methodInfo.region}</dd>
        <dt>Strength</dt><dd>{methodInfo.strength}</dd>
        <dt>Weakness</dt><dd>{methodInfo.weakness}</dd>
      </dl>
      {!isExact && (
        <p className="ctdt-note">
          The true CT → DT pole conversion for a sampled system is <Tex tex={'z = e^{sT}'} /> (ZOH and impulse-invariant
          equivalents). Forward Euler, Backward Euler and Tustin are approximations of it: compare their pole with the
          exact one above, or pick &ldquo;Exact sampling (ZOH)&rdquo; to see the samples land on the CT curve.
        </p>
      )}
    </section>
  );
}

function CTDTPolesViewer({ metadata, plots }) {
  const theme = useTheme();
  const isDark = theme !== 'light';
  const revisionRef = useRef(0);
  const revision = useMemo(() => {
    revisionRef.current += 1;
    return revisionRef.current;
  }, [plots, isDark]);

  if (!metadata || metadata.simulation_type !== 'ct_dt_poles') return null;
  const info = metadata.system_info || {};
  const byId = Object.fromEntries((plots || []).map((p) => [p.id, p]));
  const guided = metadata.guided;

  return (
    <div className="ctdt-viewer">
      {guided && (
        <div className="ctdt-guided" role="status" aria-live="polite">
          <span className="ctdt-guided__tag">Scenario {guided.index + 1}</span>
          <strong className="ctdt-guided__title">{guided.title}</strong>
          <span className="ctdt-guided__msg">{guided.message}</span>
        </div>
      )}

      <PoleCards info={info} />

      <DifferenceEquationStage eq={metadata.equations} info={info} samples={metadata.samples} />

      <div className="ctdt-plot-grid">
        {['s_plane', 'z_plane'].map((id) => byId[id] && (
          <PlotCard key={id} plot={byId[id]} isDark={isDark} revision={revision} />
        ))}
      </div>
      {['response', 'pole_vs_step'].map((id) => byId[id] && (
        <PlotCard key={id} plot={byId[id]} isDark={isDark} revision={revision} />
      ))}

      <TheoryCard methodInfo={metadata.method_info} isExact={info.method === 'exact_zoh'} />
    </div>
  );
}

export default CTDTPolesViewer;
