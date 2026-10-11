/**
 * DifferenceEquationViewer
 *
 * Custom viewer for the DT Difference Equation Step-by-Step Solver.
 * Renders:
 * - Step controls (forward, back, restart, reset, play/pause)
 * - Recursive presets: initial-condition summary (initial rest vs. y[-1]
 *   held in the feedback delay) and, with a nonzero IC, the "not LTI /
 *   incrementally linear" note.  Non-recursive presets: a note that the
 *   equation needs no auxiliary conditions (O&W Sec. 2.4.2)
 * - Equation substitution panel with highlighted current step
 * - SVG block diagram with wire values (the delay shows the stored IC)
 * - Growing stem plots for x[n] and y[n]
 * - Optional zero-input + zero-state decomposition
 *
 * Textbook conventions: Oppenheim & Willsky Sec. 2.4.2 / 1.6.6,
 * Oppenheim & Schafer Sec. 2.5, Lathi Ch. 3.
 */

import React, { useCallback, useMemo, useRef, useEffect, useState } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import PlotDisplay from './PlotDisplay';
import '../styles/DifferenceEquationViewer.css';

// ============================================================
// Value formatting helpers
// ============================================================
const PENDING_MARK = '?'; // wire value not computed yet (a dash would read as a minus sign)

/** Wire value for the diagram: up to 3 decimals, Unicode minus (as fmtNum). */
function fmtVal(v) {
  if (v === null) return PENDING_MARK;
  if (v === undefined) return '0';
  let s = (Number.isInteger(v) || v === Math.floor(v))
    ? String(Math.round(v))
    : v.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
  if (s === '-0') s = '0';
  return s.replace('-', '−');
}

/** Number for display text: up to 6 decimals, Unicode minus. */
function fmtNum(v, digits = 6) {
  if (v === null || v === undefined || Number.isNaN(v)) return PENDING_MARK;
  const r = Number(v.toFixed(digits));
  const s = (Object.is(r, -0) ? 0 : r).toString();
  return s.replace('-', '−');
}

/** Number for LaTeX; negative operands in parentheses when asked. */
function texNum(v, paren = false) {
  if (v === null || v === undefined || Number.isNaN(v)) return '?';
  const r = Number(v.toFixed(6));
  const s = (Object.is(r, -0) ? 0 : r).toString();
  return paren && r < 0 ? `(${s})` : s;
}

/** Plain text with every ASCII hyphen as a Unicode minus, e.g. "y[-1]" -> "y[−1]". */
function prettySym(s) {
  return (s || '').replace(/-/g, '−');
}

// ============================================================
// Narrow screens: legend below the axis
// ============================================================
const NARROW_QUERY = '(max-width: 480px)';

function useNarrowScreen() {
  const [narrow, setNarrow] = useState(
    () => typeof window !== 'undefined' && !!window.matchMedia && window.matchMedia(NARROW_QUERY).matches
  );
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const mql = window.matchMedia(NARROW_QUERY);
    const onChange = () => setNarrow(mql.matches);
    onChange();
    mql.addEventListener?.('change', onChange);
    return () => mql.removeEventListener?.('change', onChange);
  }, []);
  return narrow;
}

/**
 * On a phone the plot title wraps to two lines and the top legend lands on
 * its second line; pin the legend to the bottom of the figure instead, under
 * the n axis title, with room for one legend row per entry (Plotly wraps a
 * horizontal legend to one entry per row when the plot is this narrow).
 */
function useResponsivePlot(plot, narrow) {
  return useMemo(() => {
    if (!plot || !narrow) return plot;
    const layout = plot.layout || {};
    const entries = (plot.data || []).filter(t => t.name && t.showlegend !== false).length;
    return {
      ...plot,
      layout: {
        ...layout,
        legend: {
          ...(layout.legend || {}),
          orientation: 'h', xanchor: 'left', x: 0, yref: 'container', yanchor: 'bottom', y: 0.01,
        },
        margin: { ...(layout.margin || {}), b: 56 + 19 * Math.max(entries, 1) },
      },
    };
  }, [plot, narrow]);
}

// ============================================================
// KaTeX (rendered into a ref; never via innerHTML)
// ============================================================
function Tex({ latex, display = false, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    try {
      katex.render(latex, el, { throwOnError: true, displayMode: display });
    } catch (err) {
      el.textContent = latex;
      console.warn('[DifferenceEquationViewer] KaTeX could not render:', latex, err?.message);
    }
  }, [latex, display]);
  return <span ref={ref} className={`diff-eq-tex ${className}`} />;
}

// ============================================================
// SVG Block Diagram Components
// ============================================================

/** Arrowhead marker definition */
function ArrowDefs() {
  return (
    <defs>
      <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" className="arrowhead" />
      </marker>
      <marker id="arrowhead-active" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" className="arrowhead--active" />
      </marker>
    </defs>
  );
}

/** Wire value badge (number on a wire) */
function WireValue({ x, y, value, type = 'internal' }) {
  const text = fmtVal(value);
  const w = Math.max(28, text.length * 8 + 12);
  const pending = value === null;
  const cls = pending ? 'pending' : type;
  return (
    <g>
      {pending && <title>Not computed yet: this wire needs x[0]</title>}
      <rect className={`wire-value-bg${type === 'ic' ? ' wire-value-bg--ic' : ''}${pending ? ' wire-value-bg--pending' : ''}`} x={x - w / 2} y={y - 10} width={w} height={20} />
      <text className={`wire-value wire-value--${cls}`} x={x} y={y}>{text}</text>
    </g>
  );
}

/** Badge under/over the delay: what the register holds (the IC). */
function RegisterBadge({ x, y, text }) {
  const w = Math.max(60, text.length * 6.6 + 14);
  return (
    <g className="register-badge">
      <rect className="register-badge__bg" x={x - w / 2} y={y - 10} width={w} height={20} rx="4" />
      <text className="register-badge__text" x={x} y={y}>{text}</text>
    </g>
  );
}

/** Gain block (triangle) */
function GainBlock({ x, y, label, size = 30 }) {
  const half = size / 2;
  const points = `${x - half},${y - half} ${x + half},${y} ${x - half},${y + half}`;
  return (
    <g>
      <polygon points={points} className="block block--gain" />
      <text className="block-label" x={x - 3} y={y}>{label}</text>
    </g>
  );
}

/** Delay block (rectangle) */
function DelayBlock({ x, y, width = 56, height = 30, highlight = false }) {
  return (
    <g>
      <rect
        className={`block block--delay${highlight ? ' block--delay-ic' : ''}`}
        x={x - width / 2} y={y - height / 2} width={width} height={height} rx="4"
      />
      <text className="block-label" x={x} y={y}>Delay</text>
    </g>
  );
}

/** Adder block (circle with +) */
function AdderBlock({ x, y, r = 16 }) {
  return (
    <g>
      <circle className="block block--adder" cx={x} cy={y} r={r} />
      <text className="block-label" x={x} y={y} style={{ fontSize: '16px', fontWeight: 700 }}>+</text>
    </g>
  );
}

/** Wire line with optional arrow */
function Wire({ points, arrow = true }) {
  const d = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
  return (
    <path
      className="wire"
      d={d}
      markerEnd={arrow ? 'url(#arrowhead)' : undefined}
    />
  );
}

/** Signal label (x[n] or y[n]) */
function SignalLabel({ x, y, text }) {
  return <text className="signal-label" x={x} y={y}>{text}</text>;
}

// ============================================================
// Diagram Layouts (one per preset)
//
// `ic` = { showRegister, registerText, delayOutType }: with a nonzero
// initial condition the delay is highlighted and labelled with the value it
// holds before the first step (and during step 0, when that value leaves it).
// ============================================================

/**
 * Difference Machine: y[n] = x[n] - x[n-1]
 *
 *  x[n] ────────────────────→ (+) ──→ y[n]
 *    │                         ↑
 *    └──→ [×(-1)] ──→ [Delay] ─┘
 *
 * The ×(−1) gain is ahead of the delay, so the register holds −x[n−1].
 */
function DifferenceMachineDiagram({ wireValues, ic }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* Wires */}
      {/* x[n] → adder (top path) */}
      <Wire points={[[60, 45], [300, 45]]} />
      {/* x[n] → gain (fork down) */}
      <Wire points={[[80, 45], [80, 120]]} arrow={false} />
      <Wire points={[[80, 120], [130, 120]]} />
      {/* gain → delay */}
      <Wire points={[[160, 120], [220, 120]]} />
      {/* delay → adder (up) */}
      <Wire points={[[250, 120], [316, 120]]} arrow={false} />
      <Wire points={[[316, 120], [316, 61]]} />

      {/* Blocks */}
      <GainBlock x={145} y={120} label="×(−1)" size={30} />
      <DelayBlock x={235} y={120} highlight={ic.showRegister} />
      <AdderBlock x={316} y={45} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={370} y={49} text="y[n]" />

      {/* Output arrow from adder */}
      <Wire points={[[332, 45], [365, 45]]} />

      {/* Wire values */}
      <WireValue x={180} y={45} value={w.x_in} type="input" />
      {/* y = 95 keeps the badge clear of the ×(−1) triangle (top at y = 105) */}
      <WireValue x={145} y={95} value={w.gain_out} type="internal" />
      <WireValue x={290} y={120} value={w.delay_out} type={ic.delayOutType} />
      {/* above the y[n] label (at y = 45 the badge covered the label) */}
      <WireValue x={388} y={24} value={w.adder_out} type="output" />
      {ic.showRegister && <RegisterBadge x={235} y={153} text={ic.registerText} />}

      {/* Fork dot */}
      <circle cx={80} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

/**
 * Accumulator: y[n] = x[n] + y[n-1]
 *
 *  x[n] ──→ (+) ──→ y[n]
 *             ↑
 *             └── [Delay] ←─┘
 */
function AccumulatorDiagram({ wireValues, ic }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* x[n] → adder */}
      <Wire points={[[60, 45], [184, 45]]} />
      {/* adder → y[n] */}
      <Wire points={[[216, 45], [365, 45]]} />
      {/* Fork down from output */}
      <Wire points={[[320, 45], [320, 120]]} arrow={false} />
      {/* to delay */}
      <Wire points={[[320, 120], [260, 120]]} />
      {/* delay → back up to adder */}
      <Wire points={[[225, 120], [200, 120]]} arrow={false} />
      <Wire points={[[200, 120], [200, 61]]} />

      {/* Blocks */}
      <AdderBlock x={200} y={45} />
      <DelayBlock x={243} y={120} highlight={ic.showRegister} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={375} y={49} text="y[n]" />

      {/* Wire values */}
      <WireValue x={120} y={45} value={w.x_in} type="input" />
      <WireValue x={290} y={45} value={w.adder_out} type="output" />
      <WireValue x={200} y={145} value={w.delay_out} type={ic.delayOutType} />
      {ic.showRegister && <RegisterBadge x={258} y={90} text={ic.registerText} />}

      {/* Fork dot */}
      <circle cx={320} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

/**
 * Moving Average: y[n] = (x[n] + x[n-1]) / 2
 *
 *  x[n] ──→ [×0.5] ──────→ (+) ──→ y[n]
 *    │                       ↑
 *    └──→ [Delay] ──→ [×0.5] ┘
 */
function MovingAverageDiagram({ wireValues, ic }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* Top path: x → gain0.5 → adder */}
      <Wire points={[[60, 45], [115, 45]]} />
      <Wire points={[[145, 45], [290, 45]]} />
      {/* Fork down */}
      <Wire points={[[80, 45], [80, 120]]} arrow={false} />
      {/* Bottom path: x → delay → gain0.5 → adder */}
      <Wire points={[[80, 120], [145, 120]]} />
      <Wire points={[[175, 120], [230, 120]]} />
      <Wire points={[[260, 120], [306, 120]]} arrow={false} />
      <Wire points={[[306, 120], [306, 61]]} />

      {/* Blocks */}
      <GainBlock x={130} y={45} label="×0.5" size={28} />
      <DelayBlock x={160} y={120} highlight={ic.showRegister} />
      <GainBlock x={245} y={120} label="×0.5" size={28} />
      <AdderBlock x={306} y={45} />

      {/* adder → output */}
      <Wire points={[[322, 45], [365, 45]]} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={375} y={49} text="y[n]" />

      {/* Wire values */}
      <WireValue x={90} y={25} value={w.x_in} type="input" />
      <WireValue x={220} y={45} value={w.gain1_out} type="internal" />
      {/* above the wire: the 43 px gap between Delay and ×0.5 is too narrow for values like −0.35 */}
      <WireValue x={210} y={95} value={w.delay_out} type={ic.delayOutType} />
      <WireValue x={290} y={120} value={w.gain2_out} type="internal" />
      {/* above the y[n] label (at y = 45 the badge covered the label) */}
      <WireValue x={388} y={24} value={w.adder_out} type="output" />
      {ic.showRegister && <RegisterBadge x={160} y={153} text={ic.registerText} />}

      {/* Fork dot */}
      <circle cx={80} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

/**
 * Leaky Integrator: y[n] = 0.9·y[n-1] + 0.1·x[n]
 *
 *  x[n] ──→ [×0.1] ──→ (+) ──→ y[n]
 *                        ↑
 *                        └── [×0.9] ←── [Delay] ←─┘
 */
function LeakyIntegratorDiagram({ wireValues, ic }) {
  const w = wireValues || {};
  return (
    <svg className="diff-eq-diagram-svg" viewBox="0 0 440 170" preserveAspectRatio="xMidYMid meet">
      <ArrowDefs />
      {/* x[n] → gain(0.1) */}
      <Wire points={[[60, 45], [115, 45]]} />
      {/* gain(0.1) → adder */}
      <Wire points={[[145, 45], [224, 45]]} />
      {/* adder → y[n] output */}
      <Wire points={[[256, 45], [365, 45]]} />

      {/* Feedback path: fork down from output wire */}
      <Wire points={[[320, 45], [320, 120]]} arrow={false} />
      {/* → delay (right to left flow in feedback) */}
      <Wire points={[[320, 120], [315, 120]]} />
      {/* delay → gain(0.9) */}
      <Wire points={[[255, 120], [192, 120]]} />
      {/* gain(0.9) → up to adder */}
      <Wire points={[[158, 120], [158, 85]]} arrow={false} />
      <Wire points={[[158, 85], [240, 85]]} arrow={false} />
      <Wire points={[[240, 85], [240, 61]]} />

      {/* Blocks */}
      <GainBlock x={130} y={45} label="×0.1" size={28} />
      <AdderBlock x={240} y={45} />
      <DelayBlock x={285} y={120} highlight={ic.showRegister} />
      <GainBlock x={175} y={120} label="×0.9" size={28} />

      {/* Labels */}
      <SignalLabel x={15} y={49} text="x[n]" />
      <SignalLabel x={375} y={49} text="y[n]" />

      {/* Wire values */}
      <WireValue x={90} y={25} value={w.x_in} type="input" />
      <WireValue x={185} y={45} value={w.gain_x_out} type="internal" />
      <WireValue x={340} y={80} value={w.delay_out} type={ic.delayOutType} />
      <WireValue x={120} y={100} value={w.gain_fb_out} type="internal" />
      {/* above the y[n] label (at y = 45 the badge covered the label) */}
      <WireValue x={388} y={24} value={w.adder_out} type="output" />
      {ic.showRegister && <RegisterBadge x={285} y={153} text={ic.registerText} />}

      {/* Fork dot */}
      <circle cx={320} cy={45} r={3} fill="var(--text-muted)" />
    </svg>
  );
}

// Map diagram type to component
const DIAGRAM_COMPONENTS = {
  difference_machine: DifferenceMachineDiagram,
  accumulator: AccumulatorDiagram,
  moving_average: MovingAverageDiagram,
  leaky_integrator: LeakyIntegratorDiagram,
};

// ============================================================
// Initial-condition summary + LTI note
// ============================================================

/**
 * Non-recursive (FIR) presets: y[n] depends on input samples only, so the
 * equation needs no auxiliary conditions (O&W Sec. 2.4.2) and the tool
 * offers none.
 */
function NonRecursiveNote({ hLatex }) {
  return (
    <div className="diff-eq-ic" aria-live="polite">
      <div className="diff-eq-ic__row">
        <span className="diff-eq-ic__chip">No initial conditions needed</span>
        <span className="diff-eq-ic__text">
          This equation is <em>non-recursive</em>: y[n] is a weighted sum of the input samples x[n]
          and x[n−1] only, never of past outputs, so it needs no auxiliary (initial) conditions
          (Oppenheim &amp; Willsky §2.4.2). It is an LTI FIR system with{' '}
          {hLatex ? <Tex latex={hLatex} /> : 'a finite-length h[n]'}. The input is causal, so
          x[−1] = 0 and the delay starts empty. Initial conditions apply to the recursive equations
          (Accumulator, Leaky Integrator).
        </span>
      </div>
    </div>
  );
}

function InitialConditionPanel({ icMeta }) {
  if (icMeta?.recursive === false) return <NonRecursiveNote hLatex={icMeta.h_latex} />;
  const items = icMeta?.items ?? [];
  if (!items.length) return null;
  const active = icMeta.mode === 'ic';
  const item = items[0];

  return (
    <div className={`diff-eq-ic ${active ? 'diff-eq-ic--active' : ''}`} aria-live="polite">
      <div className="diff-eq-ic__row">
        <span className={`diff-eq-ic__chip ${active ? 'diff-eq-ic__chip--active' : ''}`}>
          {active ? 'Initial condition' : 'Initial rest'}
        </span>
        <Tex latex={`${item.latex} = ${texNum(item.value)}`} className="diff-eq-ic__value" />
        <span className="diff-eq-ic__text">
          {active
            ? 'is the past output held in the feedback delay at n = 0. The recursion starts at n = 0 and reads it in the first step.'
            : `The delay starts empty (all past values are 0), so y[n] = 0 until the input arrives. Set ${prettySym(item.symbol)} under Initial Conditions to load a value into the delay.`}
        </span>
      </div>
      {active && (
        <div className="diff-eq-ic__lti" role="note">
          <strong>Not LTI with a nonzero initial condition.</strong>{' '}
          With <Tex latex="x[n] = 0" /> the output is still nonzero (the zero-input response), so the
          system is not linear; the stored value is tied to <Tex latex="n = 0" />, so it is not
          time-invariant. It is <em>incrementally linear</em>:{' '}
          <Tex latex="y[n] = y_{zi}[n] + y_{zs}[n]" />, and only <Tex latex="y_{zs} = h * x" /> is an LTI
          response. The impulse response, convolution and <Tex latex="H(z)" /> assume initial rest
          (all initial conditions 0).
        </div>
      )}
    </div>
  );
}

// ============================================================
// Zero-input + zero-state decomposition card
// ============================================================

function DecompositionPanel({ icMeta, decomposition, plot, currentN }) {
  const n = decomposition?.n ?? [];
  const last = n.length - 1;
  const atRest = icMeta?.mode !== 'ic';
  const k = last >= 0 ? n[last] : null;
  const zi = last >= 0 ? decomposition.zir[last] : null;
  const zs = last >= 0 ? decomposition.zsr[last] : null;
  const tot = last >= 0 ? decomposition.total[last] : null;

  const check = k !== null
    ? `y_{zi}[${k}] + y_{zs}[${k}] = ${texNum(zi)} + ${texNum(zs, true)} = ${texNum(tot)} = y[${k}]`
    : null;

  return (
    <div className="diff-eq-decomp">
      <div className="diff-eq-decomp__header">
        <Tex latex="y[n] = y_{zi}[n] + y_{zs}[n]" display />
      </div>
      <div className="diff-eq-decomp__legend">
        <div className="diff-eq-decomp__item">
          <span className="diff-eq-decomp__swatch diff-eq-decomp__swatch--zi" aria-hidden="true" />
          <div>
            <div className="diff-eq-decomp__name">Zero-input response: initial condition only, <Tex latex="x[n] = 0" /></div>
            <Tex latex={icMeta?.zir_latex || 'y_{zi}[n]'} />
          </div>
        </div>
        <div className="diff-eq-decomp__item">
          <span className="diff-eq-decomp__swatch diff-eq-decomp__swatch--zs" aria-hidden="true" />
          <div>
            <div className="diff-eq-decomp__name">Zero-state response: input only, initial rest</div>
            <Tex latex={`y_{zs}[n] = (h * x)[n], \\quad ${icMeta?.h_latex || 'h[n]'}`} />
          </div>
        </div>
      </div>
      <div className="diff-eq-decomp__check" aria-live="polite">
        {check ? <Tex latex={check} /> : (
          <span className="diff-eq-decomp__hint">
            {currentN < 0 && !atRest ? 'Click "Next" to compute n = 0.' : 'Step to n = 0 to start the comparison.'}
          </span>
        )}
      </div>
      {atRest && (
        <div className="diff-eq-decomp__hint">
          All initial conditions are 0 (initial rest), so <Tex latex="y_{zi}[n] = 0" /> and{' '}
          <Tex latex="y[n] = y_{zs}[n]" />. Set a nonzero initial condition to see the split.
        </div>
      )}
      <div className="diff-eq-plot-wrapper diff-eq-plot-wrapper--decomp">
        {plot ? <PlotDisplay plots={[plot]} isLoading={false} /> : null}
      </div>
      <div className="diff-eq-decomp__foot">
        The two stems at each n are drawn slightly left (zero-input) and right (zero-state) of the
        integer so both stay visible; hover shows the sample index.
      </div>
    </div>
  );
}

// ============================================================
// Main Viewer Component
// ============================================================

export default function DifferenceEquationViewer({ metadata, plots, onButtonClick, isUpdating }) {
  const stepsEndRef = useRef(null);

  const currentN = metadata?.current_n ?? -3;
  const isAtRest = metadata?.is_at_rest ?? true;
  const atStart = metadata?.at_start ?? isAtRest;
  const canStepBack = metadata?.can_step_back ?? false;
  const canStepForward = metadata?.can_step_forward ?? true;
  // Reset restores every default, so it stays enabled while any setting differs
  const canReset = metadata?.can_reset ?? !isAtRest;
  const equationText = metadata?.equation_text ?? '';
  const diagramType = metadata?.diagram_type ?? 'difference_machine';
  const wireValues = metadata?.wire_values ?? {};
  const substitutionHistory = metadata?.substitution_history ?? [];
  const inputSignalType = metadata?.input_signal_type ?? 'impulse';
  const icMeta = metadata?.initial_conditions;
  const icActive = icMeta?.mode === 'ic';
  const icItem = icMeta?.items?.[0];
  const showDecomposition = metadata?.show_decomposition ?? false;

  // Input signal display name
  const inputLabel = useMemo(() => {
    const labels = { impulse: 'x[n] = δ[n]', step: 'x[n] = u[n]', ramp: 'x[n] = n·u[n]' };
    return labels[inputSignalType] || inputSignalType;
  }, [inputSignalType]);

  // What the diagram shows about the stored initial condition
  const diagramIc = useMemo(() => {
    const holdsIc = icActive && (atStart || currentN === 0);
    const reg = icMeta?.register;
    return {
      showRegister: holdsIc,
      registerText: reg ? `${reg.ic_symbol} = ${fmtNum(reg.initial_value, 4)}` : '',
      delayOutType: holdsIc ? 'ic' : 'internal',
    };
  }, [icActive, atStart, currentN, icMeta]);

  // Auto-scroll the step list (only the list, never the page) to the newest step
  useEffect(() => {
    const list = stepsEndRef.current?.parentElement;
    if (list && typeof list.scrollTo === 'function') {
      list.scrollTo({ top: list.scrollHeight, behavior: 'smooth' });
    }
  }, [substitutionHistory.length]);

  // Button handlers
  const handleStepForward = useCallback(() => {
    onButtonClick?.('step_forward');
  }, [onButtonClick]);

  const handleStepBackward = useCallback(() => {
    onButtonClick?.('step_backward');
  }, [onButtonClick]);

  const handleRestart = useCallback(() => {
    onButtonClick?.('restart');
  }, [onButtonClick]);

  const handleReset = useCallback(() => {
    onButtonClick?.('reset');
  }, [onButtonClick]);

  const handlePlayPause = useCallback(() => {
    onButtonClick?.('play_pause');
  }, [onButtonClick]);

  // Get the right diagram component
  const DiagramComponent = DIAGRAM_COMPONENTS[diagramType] || DifferenceMachineDiagram;

  // Split plots for the stem plot areas (legend moved under the axis on phones)
  const narrow = useNarrowScreen();
  const inputPlot = useResponsivePlot(plots?.find(p => p.id === 'input_signal'), narrow);
  const outputPlot = useResponsivePlot(plots?.find(p => p.id === 'output_signal'), narrow);
  const decompPlot = useResponsivePlot(plots?.find(p => p.id === 'decomposition'), narrow);

  const nLabel = prettySym(String(currentN));
  const stepInfo = atStart ? (icActive ? 'Initial state' : 'At Rest') : `n = ${nLabel}`;
  let diagramTitle;
  if (!atStart) diagramTitle = `Block Diagram — n = ${nLabel}`;
  else if (icActive) diagramTitle = `Block Diagram — initial state: the delay holds ${prettySym(icMeta?.register?.ic_symbol || '')}`;
  else diagramTitle = 'Block Diagram (at rest)';

  return (
    <div className="diff-eq-viewer">
      {/* Step Controls */}
      <div className="diff-eq-controls" role="toolbar" aria-label="Step controls">
        <button
          className="diff-eq-controls__btn"
          onClick={handleReset}
          disabled={isUpdating || !canReset}
          aria-label="Reset all settings to defaults"
          title="Reset all settings to defaults"
        >
          &#x21BA; Reset
        </button>
        <button
          className="diff-eq-controls__btn"
          onClick={handleRestart}
          disabled={isUpdating || atStart}
          aria-label="Restart from the first step, keeping the settings"
          title="Restart from the first step (keeps the equation, input and initial conditions)"
        >
          &#x23EE; Restart
        </button>
        <button
          className="diff-eq-controls__btn"
          onClick={handleStepBackward}
          disabled={isUpdating || !canStepBack}
          aria-label="Step backward"
          title="Step Back"
        >
          &#x25C0; Back
        </button>
        <button
          className="diff-eq-controls__btn diff-eq-controls__btn--primary"
          onClick={handleStepForward}
          disabled={isUpdating || !canStepForward}
          aria-label="Step forward"
          title="Step Forward"
        >
          Next &#x25B6;
        </button>
        <button
          className="diff-eq-controls__btn"
          onClick={handlePlayPause}
          disabled={isUpdating}
          aria-label="Play or pause animation"
          title="Auto-play"
        >
          &#x25B6;&#x25B6; Play
        </button>

        <div className="diff-eq-controls__spacer" />

        <div
          className={`diff-eq-controls__step-info ${atStart ? 'diff-eq-controls__step-info--at-rest' : ''}`}
          aria-live="polite"
        >
          {stepInfo}
        </div>
      </div>

      {/* Initial conditions (recursive presets) / no-IC note (non-recursive) */}
      <InitialConditionPanel icMeta={icMeta} />

      {/* Top Panels: Equation + Block Diagram */}
      <div className="diff-eq-panels">
        {/* Equation Panel */}
        <div className="diff-eq-equation-panel">
          <div className="diff-eq-equation-panel__header">
            {equationText} &nbsp;&nbsp;|&nbsp;&nbsp; {inputLabel}
          </div>
          {substitutionHistory.length > 0 ? (
            <div className="diff-eq-equation-panel__steps" role="log" aria-label="Step history">
              {substitutionHistory.map((step, idx) => {
                const isCurrent = idx === substitutionHistory.length - 1;
                const isZero = step.result === 0;
                const icTerms = step.ic_terms ?? [];
                const icTitle = icTerms.length
                  ? icTerms.map(t => `${prettySym(t.symbol)} = ${fmtNum(t.value)}`).join(', ') + ' is the initial condition (stored in the delay)'
                  : undefined;
                return (
                  <div
                    key={step.n}
                    className={`diff-eq-step ${isCurrent ? 'diff-eq-step--current' : ''} ${isZero && !isCurrent ? 'diff-eq-step--zero' : ''} ${icTerms.length ? 'diff-eq-step--ic' : ''}`}
                    title={icTitle}
                  >
                    {icTerms.length > 0 && <span className="diff-eq-step__ic-tag">IC</span>}
                    {/* one minus glyph (U+2212) throughout, as in the equation header */}
                    {prettySym(step.text)}
                  </div>
                );
              })}
              <div ref={stepsEndRef} />
            </div>
          ) : (
            <div className="diff-eq-equation-panel__empty">
              {icActive && icItem
                ? `Click "Next" to compute y[0] from x[0] and the initial condition ${prettySym(icItem.symbol)} = ${fmtNum(icItem.value)}`
                : 'Click "Next" to start stepping through the equation'}
            </div>
          )}
        </div>

        {/* Block Diagram Panel */}
        <div className="diff-eq-diagram-panel">
          <div className="diff-eq-diagram-panel__title">
            {diagramTitle}
          </div>
          <DiagramComponent wireValues={wireValues} ic={diagramIc} />
        </div>
      </div>

      {/* Stem Plots */}
      <div className="diff-eq-plots">
        <div className="diff-eq-plot-wrapper">
          {inputPlot ? (
            <PlotDisplay plots={[inputPlot]} isLoading={false} />
          ) : (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              Input signal plot
            </div>
          )}
        </div>
        <div className="diff-eq-plot-wrapper">
          {outputPlot ? (
            <PlotDisplay plots={[outputPlot]} isLoading={false} />
          ) : (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
              Output signal plot
            </div>
          )}
        </div>
      </div>

      {/* Zero-input + zero-state decomposition */}
      {showDecomposition && (
        <DecompositionPanel
          icMeta={icMeta}
          decomposition={metadata?.decomposition}
          plot={decompPlot}
          currentN={currentN}
        />
      )}
    </div>
  );
}
