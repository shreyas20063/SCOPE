/**
 * HubPanel.jsx
 *
 * Floating side panel for the System Hub. Slides in from the right.
 * Displays the control slot with TF/SS data, poles, zeros, and properties.
 *
 * KaTeX rendering follows the same trusted pattern used in RootLocusViewer,
 * ControllerTuningLabViewer, BlockDiagramViewer, etc. KaTeX.renderToString
 * produces sanitized HTML output.
 */

import React, { useMemo, useCallback } from 'react';
import { useHubContext } from '../contexts/HubContext';
import katex from 'katex';
import '../styles/Hub.css';

// Single-slot hub — only control data flows through the Design Pipeline

/**
 * Safely render a LaTeX string to HTML via KaTeX.
 * Falls back to null if KaTeX is unavailable or throws.
 */
function renderKatex(latex, displayMode = false) {
  try {
    return katex.renderToString(latex, { throwOnError: false, displayMode });
  } catch {
    return null;
  }
}

/**
 * Format a complex number for display.
 */
function formatComplex(val) {
  if (val == null) return '?';
  if (typeof val === 'number') return val.toFixed(4);
  if (typeof val === 'string') return val;
  // Object with real/imag
  if (val.real !== undefined && val.imag !== undefined) {
    const r = val.real.toFixed(4);
    if (Math.abs(val.imag) < 1e-10) return r;
    const sign = val.imag >= 0 ? '+' : '-';
    return `${r} ${sign} ${Math.abs(val.imag).toFixed(4)}j`;
  }
  return String(val);
}

/**
 * Build a LaTeX polynomial string from coefficient array.
 * Coefficients are ordered highest degree first: [a_n, a_{n-1}, ..., a_0]
 */
function polyToLatex(coeffs, variable = 's') {
  if (!coeffs || !coeffs.length) return '0';
  const n = coeffs.length - 1;
  const terms = [];
  for (let i = 0; i <= n; i++) {
    const c = coeffs[i];
    const power = n - i;
    if (Math.abs(c) < 1e-15) continue;

    let coefStr = '';
    if (power === 0 || Math.abs(Math.abs(c) - 1) > 1e-10) {
      coefStr = Number.isInteger(c) ? String(Math.abs(c)) : Math.abs(c).toFixed(4).replace(/\.?0+$/, '');
    }

    let term = '';
    if (power === 0) {
      term = coefStr || '1';
    } else if (power === 1) {
      term = coefStr ? `${coefStr}${variable}` : variable;
    } else {
      term = coefStr ? `${coefStr}${variable}^{${power}}` : `${variable}^{${power}}`;
    }

    if (terms.length === 0) {
      terms.push(c < 0 ? `-${term}` : term);
    } else {
      terms.push(c < 0 ? `- ${term}` : `+ ${term}`);
    }
  }
  return terms.length > 0 ? terms.join(' ') : '0';
}

/**
 * Build KaTeX bmatrix string from a 2D array.
 */
function matrixToLatex(mat) {
  if (!mat || !mat.length) return '';
  const rows = mat.map(row =>
    row.map(v => {
      if (typeof v === 'number') {
        return Number.isInteger(v) ? String(v) : v.toFixed(4).replace(/\.?0+$/, '');
      }
      return String(v);
    }).join(' & ')
  ).join(' \\\\ ');
  return `\\begin{bmatrix} ${rows} \\end{bmatrix}`;
}


/* ====================================================================
   Slot Views
   ==================================================================== */

function ControlSlotView({ data }) {
  // Enriched data uses flat keys: tf, ss, poles, zeros, stable, etc.
  const { tf, ss, poles, zeros, domain, dimensions, order, system_type,
          stable, controllable, observable, controller, transfer_matrix,
          _meta, _validationWarning } = data;

  // Transfer function LaTeX (SISO or 1x1 compat)
  const tfHtml = useMemo(() => {
    if (!tf?.num && !tf?.den) return null;
    const variable = tf.variable || (domain === 'dt' ? 'z' : 's');
    const numLatex = polyToLatex(tf.num, variable);
    const denLatex = polyToLatex(tf.den, variable);
    const fnName = domain === 'dt' ? 'H' : 'G';
    const latex = `${fnName}(${variable}) = \\frac{${numLatex}}{${denLatex}}`;
    return renderKatex(latex, true);
  }, [tf, domain]);

  // MIMO transfer matrix entries
  const mimoEntries = useMemo(() => {
    if (!transfer_matrix?.entries?.length) return null;
    const { entries, input_labels, output_labels, variable: v } = transfer_matrix;
    const varName = v || (domain === 'dt' ? 'z' : 's');
    const items = [];
    for (let i = 0; i < entries.length; i++) {
      for (let j = 0; j < entries[i].length; j++) {
        const e = entries[i][j];
        const numL = polyToLatex(e.num, varName);
        const denL = polyToLatex(e.den, varName);
        const sub = `${i + 1}${j + 1}`;
        const latex = `G_{${sub}}(${varName}) = \\frac{${numL}}{${denL}}`;
        items.push({
          html: renderKatex(latex, true),
          stable: e.stable,
          outLabel: output_labels?.[i] || `y${i + 1}`,
          inLabel: input_labels?.[j] || `u${j + 1}`,
        });
      }
    }
    return items;
  }, [transfer_matrix, domain]);

  // State-space matrices LaTeX
  const ssHtml = useMemo(() => {
    if (!ss) return null;
    const parts = [];
    if (ss.A) parts.push(`\\mathbf{A} = ${matrixToLatex(ss.A)}`);
    if (ss.B) parts.push(`\\mathbf{B} = ${matrixToLatex(ss.B)}`);
    if (ss.C) parts.push(`\\mathbf{C} = ${matrixToLatex(ss.C)}`);
    if (ss.D) parts.push(`\\mathbf{D} = ${matrixToLatex(ss.D)}`);
    if (parts.length === 0) return null;
    return parts.map(p => renderKatex(p, true));
  }, [ss]);

  // Format dimensions string
  const dimsLabel = useMemo(() => {
    if (!dimensions) return null;
    const { n, m, p } = dimensions;
    if (m === 1 && p === 1) return `SISO (order ${n || order || '?'})`;
    return `${p}\u00d7${m} MIMO (n=${n || order || '?'})`;
  }, [dimensions, order]);

  return (
    <div className="hub-slot__content">
      {/* Validation warning */}
      {_validationWarning && (
        <div className="hub-slot__warning">
          <span className="hub-slot__warning-icon">{'\u26A0'}</span>
          <span>{_validationWarning}</span>
        </div>
      )}

      {/* Source info */}
      {_meta && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Source</div>
          <div className="hub-slot__value">{_meta.pushed_by || 'Unknown'}</div>
          {(domain || dimsLabel) && (
            <div className="hub-slot__meta-row">
              {domain && (
                <span className="hub-prop__badge--info">{domain === 'ct' ? 'Continuous' : 'Discrete'}</span>
              )}
              {dimsLabel && (
                <span className="hub-prop__badge--info">{dimsLabel}</span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Transfer Function */}
      {tfHtml && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Transfer Function</div>
          <div
            className="hub-slot__katex"
            dangerouslySetInnerHTML={{ __html: tfHtml }}
          />
        </div>
      )}

      {/* MIMO Transfer Matrix */}
      {mimoEntries && mimoEntries.length > 0 && !tfHtml && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Transfer Matrix</div>
          <div className="hub-mimo-entries">
            {mimoEntries.map((entry, i) => (
              <div key={i} className="hub-mimo-entry">
                <div className="hub-mimo-entry__header">
                  <span className={`hub-mimo-dot hub-mimo-dot--${entry.stable ? 'stable' : 'unstable'}`} />
                  <span className="hub-mimo-path">{entry.outLabel} {'\u2190'} {entry.inLabel}</span>
                </div>
                {entry.html && (
                  <div
                    className="hub-slot__katex hub-slot__katex--compact"
                    dangerouslySetInnerHTML={{ __html: entry.html }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* State-Space Matrices */}
      {ssHtml && ssHtml.length > 0 && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">State-Space</div>
          {ssHtml.map((html, i) => html && (
            <div
              key={i}
              className="hub-slot__katex"
              style={{ marginBottom: i < ssHtml.length - 1 ? '8px' : 0 }}
              dangerouslySetInnerHTML={{ __html: html }}
            />
          ))}
        </div>
      )}

      {/* Properties Grid */}
      {(order != null || system_type != null || stable != null || controllable != null || observable != null) && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Properties</div>
          <div className="hub-slot__props">
            {order != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Order</span>
                <span className="hub-prop__val">{order}</span>
              </div>
            )}
            {system_type != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">System Type</span>
                <span className="hub-prop__val">{system_type}</span>
              </div>
            )}
            {stable != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Stable</span>
                <span className={`hub-prop__badge--${stable ? 'success' : 'danger'}`}>
                  {stable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
            {controllable != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Controllable</span>
                <span className={`hub-prop__badge--${controllable ? 'success' : 'danger'}`}>
                  {controllable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
            {observable != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Observable</span>
                <span className={`hub-prop__badge--${observable ? 'success' : 'danger'}`}>
                  {observable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Poles & Zeros */}
      {(poles?.length > 0 || zeros?.length > 0) && (
        <div className="hub-slot__section">
          {poles?.length > 0 && (
            <>
              <div className="hub-slot__label">Poles</div>
              <div className="hub-slot__chips">
                {poles.map((p, i) => (
                  <span key={`pole-${i}`} className="hub-pole hub-pole--pole">
                    {formatComplex(p)}
                  </span>
                ))}
              </div>
            </>
          )}
          {zeros?.length > 0 && (
            <>
              <div className="hub-slot__label" style={{ marginTop: '8px' }}>Zeros</div>
              <div className="hub-slot__chips">
                {zeros.map((z, i) => (
                  <span key={`zero-${i}`} className="hub-pole hub-pole--zero">
                    {formatComplex(z)}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Controller Layer */}
      {controller && (
        <div className={`hub-slot__section${controller.stale ? ' hub-slot__section--stale' : ''}`}>
          <div className="hub-slot__label">
            Controller
            {controller.stale && <span className="hub-stale-badge">STALE</span>}
          </div>
          {controller.type && (
            <div className="hub-prop">
              <span className="hub-prop__key">Type</span>
              <span className="hub-prop__val">{controller.type}</span>
            </div>
          )}
          {controller.gains && (
            <div className="hub-prop">
              <span className="hub-prop__key">Gains</span>
              <span className="hub-prop__val" style={{ fontFamily: 'var(--font-mono)' }}>
                {JSON.stringify(controller.gains)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


function EmptySlot() {
  return (
    <div className="hub-slot__empty">
      <div className="hub-slot__empty-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.3 }}>
          <circle cx="12" cy="12" r="3"/>
          <line x1="12" y1="2" x2="12" y2="9"/>
          <line x1="12" y1="15" x2="12" y2="22"/>
          <line x1="2" y1="12" x2="9" y2="12"/>
          <line x1="15" y1="12" x2="22" y2="12"/>
        </svg>
      </div>
      <p>No data in hub</p>
      <p className="hub-slot__hint">Push a transfer function or state-space model from any Control Systems simulation.</p>
      <p className="hub-slot__hint" style={{ marginTop: '8px' }}>
        Try: Root Locus, Second Order System, Bode/Nyquist, Controller Tuning Lab
      </p>
    </div>
  );
}


/* ====================================================================
   Main HubPanel
   ==================================================================== */

function HubPanel({ isOpen, onClose }) {
  const { hubState, clearSlot } = useHubContext();

  const controlData = hubState.control;

  const handleClear = useCallback(() => {
    clearSlot('control');
  }, [clearSlot]);

  const handleExportJSON = useCallback(() => {
    if (!controlData) return;
    const json = JSON.stringify(controlData, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hub-control-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [controlData]);

  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="hub-backdrop"
          onClick={handleBackdropClick}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div className={`hub-panel${isOpen ? ' hub-panel--open' : ''}`}>
        {/* Header */}
        <div className="hub-panel__header">
          <h3 className="hub-panel__title">System Hub</h3>
          <button
            className="hub-panel__close"
            onClick={onClose}
            aria-label="Close Hub"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Slot Content */}
        <div className="hub-panel__body">
          {controlData ? <ControlSlotView data={controlData} /> : <EmptySlot />}
        </div>

        {/* Footer */}
        <div className="hub-panel__footer">
          <button
            className="hub-action hub-action--danger"
            onClick={handleClear}
            disabled={!controlData}
          >
            Clear
          </button>
          <button
            className="hub-action"
            onClick={handleExportJSON}
            disabled={!controlData}
          >
            Export JSON
          </button>
        </div>
      </div>
    </>
  );
}

export default HubPanel;
