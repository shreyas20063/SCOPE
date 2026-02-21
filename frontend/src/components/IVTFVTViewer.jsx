/**
 * IVTFVTViewer Component
 *
 * Custom viewer for the Initial & Final Value Theorem Visualizer.
 * Displays equation banner, theorem validity cards, failure mode warnings,
 * and a 2+1 plot layout (signal + kernel side-by-side, product full width).
 */

import React, { useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/IVTFVTViewer.css';

function IVTFVTViewer({ metadata, plots, isUpdating }) {
  // Filter plots by ID
  const signalPlot = useMemo(
    () => plots?.filter(p => p.id === 'signal_xt') || [],
    [plots]
  );
  const kernelPlot = useMemo(
    () => plots?.filter(p => p.id === 'kernel_set') || [],
    [plots]
  );
  const productPlot = useMemo(
    () => plots?.filter(p => p.id === 'product_integral') || [],
    [plots]
  );

  const sValue = metadata?.s_value ?? 1.0;
  const sXsNumerical = metadata?.sXs_numerical;
  const isFailure = metadata?.is_failure_mode ?? false;
  const ivtValid = metadata?.ivt_valid ?? true;
  const fvtValid = metadata?.fvt_valid ?? true;
  const x0Plus = metadata?.x_0_plus;
  const xInfDisplay = metadata?.x_inf_display ?? '—';

  const ivtColor = ivtValid ? 'var(--success-color)' : 'var(--error-color)';
  const fvtColor = fvtValid ? 'var(--success-color)' : 'var(--error-color)';

  return (
    <div className="ivt-fvt-viewer">
      {/* Equation banner */}
      <div className="ivt-equation-banner">
        <div className="ivt-formula-group">
          <span className="ivt-label">Signal:</span>
          <span className="ivt-expression">{metadata?.active_signal_label || '—'}</span>
        </div>
        <span className="ivt-formula-divider" />
        <div className="ivt-formula-group">
          <span className="ivt-label">X(s) =</span>
          <span className="ivt-expression">{metadata?.Xs_formula || '—'}</span>
        </div>
        <span className="ivt-formula-divider" />
        <div className="ivt-formula-group">
          <span className="ivt-label">sX(s) =</span>
          <span className="ivt-expression">{metadata?.sXs_formula || '—'}</span>
        </div>
      </div>

      {/* Info cards row */}
      <div className="ivt-info-row">
        {/* IVT Card */}
        <div className="ivt-info-card" style={{ borderLeftColor: ivtColor }}>
          <span className="ivt-card-label">Initial Value Theorem</span>
          <div className="ivt-card-row">
            <span className="ivt-card-key">x(0⁺)</span>
            <span className="ivt-card-val">
              {x0Plus != null ? Number(x0Plus).toFixed(4) : '—'}
            </span>
          </div>
          <div className="ivt-card-row">
            <span className="ivt-card-key">lim sX(s), s→∞</span>
            <span className="ivt-card-val">
              {metadata?.ivt_limit != null ? Number(metadata.ivt_limit).toFixed(4) : '—'}
            </span>
          </div>
          <span
            className="ivt-validity-badge"
            style={{
              background: ivtValid ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              color: ivtColor,
              borderColor: ivtValid ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)',
            }}
          >
            {ivtValid ? '✓ VALID' : '✗ INVALID'}
          </span>
        </div>

        {/* FVT Card */}
        <div className="ivt-info-card" style={{ borderLeftColor: fvtColor }}>
          <span className="ivt-card-label">Final Value Theorem</span>
          <div className="ivt-card-row">
            <span className="ivt-card-key">x(∞)</span>
            <span className="ivt-card-val">{xInfDisplay}</span>
          </div>
          <div className="ivt-card-row">
            <span className="ivt-card-key">lim sX(s), s→0</span>
            <span className="ivt-card-val">
              {metadata?.fvt_limit != null ? Number(metadata.fvt_limit).toFixed(4) : '—'}
            </span>
          </div>
          <span
            className="ivt-validity-badge"
            style={{
              background: fvtValid ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              color: fvtColor,
              borderColor: fvtValid ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)',
            }}
          >
            {fvtValid ? '✓ VALID' : '✗ FAILS'}
          </span>
        </div>

        {/* Current Value Card */}
        <div className="ivt-info-card" style={{ borderLeftColor: 'var(--primary-color)' }}>
          <span className="ivt-card-label">Current Value</span>
          <div className="ivt-card-row">
            <span className="ivt-card-key">s</span>
            <span className="ivt-card-val">{Number(sValue).toFixed(3)}</span>
          </div>
          <div className="ivt-card-row">
            <span className="ivt-card-key">sX(s)</span>
            <span className="ivt-card-val" style={{ color: 'var(--accent-color)' }}>
              {sXsNumerical != null ? Number(sXsNumerical).toFixed(4) : '—'}
            </span>
          </div>
          {metadata?.sXs_analytical != null && (
            <div className="ivt-card-row">
              <span className="ivt-card-key">analytical</span>
              <span className="ivt-card-val" style={{ color: 'var(--text-secondary)' }}>
                {Number(metadata.sXs_analytical).toFixed(4)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Failure mode warning banner */}
      {isFailure && metadata?.fvt_reason && (
        <div className="ivt-failure-banner" role="alert" aria-live="polite">
          <span className="ivt-failure-icon">⚠ Warning</span>
          <span className="ivt-failure-text">{metadata.fvt_reason}</span>
        </div>
      )}

      {/* Signal + Kernel side-by-side */}
      <div className="ivt-plots-row">
        <div className="ivt-plot-half">
          <PlotDisplay plots={signalPlot} isLoading={false} />
        </div>
        <div className="ivt-plot-half">
          <PlotDisplay plots={kernelPlot} isLoading={false} />
        </div>
      </div>

      {/* Product plot (full width) */}
      <div className="ivt-plot-product">
        <PlotDisplay plots={productPlot} isLoading={false} />
      </div>
    </div>
  );
}

export default IVTFVTViewer;
