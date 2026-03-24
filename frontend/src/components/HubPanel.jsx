/**
 * HubPanel.jsx
 *
 * Floating side panel for the System Hub. Slides in from the right.
 * Displays 4 slot tabs (Control, Signal, Circuit, Optics) with
 * detailed views for each slot type.
 *
 * KaTeX rendering follows the same trusted pattern used in RootLocusViewer,
 * ControllerTuningLabViewer, BlockDiagramViewer, etc. KaTeX.renderToString
 * produces sanitized HTML output.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useHubContext } from '../contexts/HubContext';
import katex from 'katex';
import '../styles/Hub.css';

const SLOT_TABS = [
  { key: 'control', label: 'Control' },
  { key: 'signal', label: 'Signal' },
  { key: 'circuit', label: 'Circuit' },
  { key: 'optics', label: 'Optics' },
];

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
  const { plant, state_space, properties, controller, _meta } = data;

  // Transfer function LaTeX
  const tfHtml = useMemo(() => {
    if (!plant?.numerator && !plant?.denominator) return null;
    const numLatex = polyToLatex(plant.numerator);
    const denLatex = polyToLatex(plant.denominator);
    const latex = `G(s) = \\frac{${numLatex}}{${denLatex}}`;
    return renderKatex(latex, true);
  }, [plant?.numerator, plant?.denominator]);

  // State-space matrices LaTeX
  const ssHtml = useMemo(() => {
    if (!state_space) return null;
    const parts = [];
    if (state_space.A) parts.push(`\\mathbf{A} = ${matrixToLatex(state_space.A)}`);
    if (state_space.B) parts.push(`\\mathbf{B} = ${matrixToLatex(state_space.B)}`);
    if (state_space.C) parts.push(`\\mathbf{C} = ${matrixToLatex(state_space.C)}`);
    if (state_space.D) parts.push(`\\mathbf{D} = ${matrixToLatex(state_space.D)}`);
    if (parts.length === 0) return null;
    return parts.map(p => renderKatex(p, true));
  }, [state_space]);

  return (
    <div className="hub-slot__content">
      {/* Source info */}
      {_meta && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Source</div>
          <div className="hub-slot__value">{_meta.pushed_by || 'Unknown'}</div>
          {(plant?.domain || plant?.dimensions) && (
            <div className="hub-slot__meta-row">
              {plant?.domain && (
                <span className="hub-prop__badge--info">{plant.domain === 'CT' ? 'Continuous' : 'Discrete'}</span>
              )}
              {plant?.dimensions && (
                <span className="hub-prop__badge--info">{plant.dimensions}</span>
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
      {properties && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Properties</div>
          <div className="hub-slot__props">
            {properties.order != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Order</span>
                <span className="hub-prop__val">{properties.order}</span>
              </div>
            )}
            {properties.system_type != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">System Type</span>
                <span className="hub-prop__val">{properties.system_type}</span>
              </div>
            )}
            {properties.stable != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Stable</span>
                <span className={`hub-prop__badge--${properties.stable ? 'success' : 'danger'}`}>
                  {properties.stable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
            {properties.controllable != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Controllable</span>
                <span className={`hub-prop__badge--${properties.controllable ? 'success' : 'danger'}`}>
                  {properties.controllable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
            {properties.observable != null && (
              <div className="hub-prop">
                <span className="hub-prop__key">Observable</span>
                <span className={`hub-prop__badge--${properties.observable ? 'success' : 'danger'}`}>
                  {properties.observable ? 'Yes' : 'No'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Poles & Zeros */}
      {(plant?.poles?.length > 0 || plant?.zeros?.length > 0) && (
        <div className="hub-slot__section">
          {plant.poles?.length > 0 && (
            <>
              <div className="hub-slot__label">Poles</div>
              <div className="hub-slot__chips">
                {plant.poles.map((p, i) => (
                  <span key={`pole-${i}`} className="hub-pole hub-pole--pole">
                    {formatComplex(p)}
                  </span>
                ))}
              </div>
            </>
          )}
          {plant.zeros?.length > 0 && (
            <>
              <div className="hub-slot__label" style={{ marginTop: '8px' }}>Zeros</div>
              <div className="hub-slot__chips">
                {plant.zeros.map((z, i) => (
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

function SignalSlotView({ data }) {
  const { signals, _meta } = data;

  return (
    <div className="hub-slot__content">
      {_meta && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Source</div>
          <div className="hub-slot__value">{_meta.pushed_by || 'Unknown'}</div>
        </div>
      )}
      {signals && signals.length > 0 ? (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Signals</div>
          {signals.map((sig, i) => (
            <div key={i} className="hub-prop">
              <span className="hub-prop__key">{sig.name || `Signal ${i + 1}`}</span>
              <span className="hub-prop__val">
                {sig.samples ? `${sig.samples} samples` : ''}
                {sig.sample_rate ? ` @ ${sig.sample_rate} Hz` : ''}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Signals</div>
          <div className="hub-prop">
            <span className="hub-prop__val">Signal data available</span>
          </div>
        </div>
      )}
    </div>
  );
}

function CircuitSlotView({ data }) {
  const { topology, components, _meta } = data;

  return (
    <div className="hub-slot__content">
      {_meta && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Source</div>
          <div className="hub-slot__value">{_meta.pushed_by || 'Unknown'}</div>
        </div>
      )}
      {topology && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Topology</div>
          <div className="hub-slot__value">{topology}</div>
        </div>
      )}
      {components && Object.keys(components).length > 0 && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Components</div>
          {Object.entries(components).map(([name, value]) => (
            <div key={name} className="hub-prop">
              <span className="hub-prop__key">{name}</span>
              <span className="hub-prop__val" style={{ fontFamily: 'var(--font-mono)' }}>
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function OpticsSlotView({ data }) {
  const { elements, _meta } = data;

  return (
    <div className="hub-slot__content">
      {_meta && (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Source</div>
          <div className="hub-slot__value">{_meta.pushed_by || 'Unknown'}</div>
        </div>
      )}
      {elements && elements.length > 0 ? (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Optical Elements</div>
          {elements.map((el, i) => (
            <div key={i} className="hub-prop">
              <span className="hub-prop__key">{el.type || `Element ${i + 1}`}</span>
              <span className="hub-prop__val">
                {el.focal_length != null ? `f = ${el.focal_length}` : ''}
                {el.position != null ? ` @ ${el.position}` : ''}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="hub-slot__section">
          <div className="hub-slot__label">Elements</div>
          <div className="hub-prop">
            <span className="hub-prop__val">Optics data available</span>
          </div>
        </div>
      )}
    </div>
  );
}

function EmptySlot({ slotKey }) {
  const hints = {
    control: 'Push a transfer function or state-space model from any Control Systems simulation.',
    signal: 'Push signal data from Signal Processing simulations.',
    circuit: 'Push circuit topology from Circuit simulations.',
    optics: 'Push optical elements from Optics simulations.',
  };

  return (
    <div className="hub-slot__empty">
      <p>No data in this slot</p>
      <p className="hub-slot__hint">{hints[slotKey] || 'Push data from a simulation to populate this slot.'}</p>
    </div>
  );
}


/* ====================================================================
   Main HubPanel
   ==================================================================== */

function HubPanel({ isOpen, onClose }) {
  const { hubState, clearSlot } = useHubContext();
  const [activeTab, setActiveTab] = useState('control');

  const activeData = hubState[activeTab];

  const handleClearSlot = useCallback(() => {
    clearSlot(activeTab);
  }, [clearSlot, activeTab]);

  const handleExportJSON = useCallback(() => {
    if (!activeData) return;
    const json = JSON.stringify(activeData, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hub-${activeTab}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [activeData, activeTab]);

  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  // Render the appropriate slot view
  const slotView = useMemo(() => {
    if (!activeData) return <EmptySlot slotKey={activeTab} />;

    switch (activeTab) {
      case 'control':
        return <ControlSlotView data={activeData} />;
      case 'signal':
        return <SignalSlotView data={activeData} />;
      case 'circuit':
        return <CircuitSlotView data={activeData} />;
      case 'optics':
        return <OpticsSlotView data={activeData} />;
      default:
        return <EmptySlot slotKey={activeTab} />;
    }
  }, [activeTab, activeData]);

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

        {/* Tabs */}
        <div className="hub-panel__tabs">
          {SLOT_TABS.map(tab => (
            <button
              key={tab.key}
              className={`hub-tab${activeTab === tab.key ? ' hub-tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
              {hubState[tab.key] && <span className="hub-tab__dot" />}
            </button>
          ))}
        </div>

        {/* Slot Content */}
        <div className="hub-panel__body">
          {slotView}
        </div>

        {/* Footer */}
        <div className="hub-panel__footer">
          <button
            className="hub-action hub-action--danger"
            onClick={handleClearSlot}
            disabled={!activeData}
          >
            Clear Slot
          </button>
          <button
            className="hub-action"
            onClick={handleExportJSON}
            disabled={!activeData}
          >
            Export JSON
          </button>
        </div>
      </div>
    </>
  );
}

export default HubPanel;
