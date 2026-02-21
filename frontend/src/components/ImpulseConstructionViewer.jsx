/**
 * ImpulseConstructionViewer
 *
 * Custom viewer for the Unit Impulse Construction Lab.
 * Shows header banner with equation/area badge, mode-aware plot filtering,
 * and an explanation panel for contrast mode.
 */

import React, { useMemo } from 'react';
import PlotDisplay from './PlotDisplay';
import '../styles/ImpulseConstructionViewer.css';

function HeaderBanner({ metadata }) {
  if (!metadata) return null;
  const { epsilon, pulse_height, area, mode, system_pole } = metadata;

  const modeLabels = {
    construction: 'Delta Construction',
    system_response: 'System Response',
    contrast: 'Contrast Panel',
  };

  return (
    <div className="ic-header-banner">
      <div className="ic-equation">
        <span className="ic-equation-label">Pulse:</span>
        <span className="ic-equation-math">
          p<sub>&epsilon;</sub>(t) = {pulse_height?.toFixed(2)} &nbsp;for&nbsp; |t| &le; {epsilon?.toFixed(3)}
        </span>
      </div>
      <div className="ic-badges">
        <span className="ic-mode-badge">{modeLabels[mode] || mode}</span>
        <span className="ic-area-badge">Area = {area?.toFixed(3)}</span>
        {mode === 'system_response' && system_pole != null && (
          <span className="ic-pole-badge">p = {system_pole?.toFixed(1)}</span>
        )}
      </div>
    </div>
  );
}

function ContrastExplanation() {
  return (
    <div className="ic-contrast-explanation">
      <p>
        <strong>Why w(t) = 1 at t = 0 fails:</strong> A single point has zero width,
        so its Lebesgue integral is zero &mdash; not one. The rectangular pulse p<sub>&epsilon;</sub>(t)
        maintains unit area at <em>every</em> stage of the limiting process. That is the
        essential property that makes it a valid approximation to &delta;(t).
      </p>
    </div>
  );
}

function ImpulseConstructionViewer({ metadata, plots }) {
  const mode = metadata?.mode || 'construction';

  const filteredPlots = useMemo(() => {
    if (!plots) return [];
    if (mode === 'construction') {
      return plots.filter(p => p.id === 'pulse_plot' || p.id === 'integral_plot');
    } else if (mode === 'system_response') {
      return plots.filter(p => p.id === 'pulse_plot' || p.id === 'system_output');
    } else if (mode === 'contrast') {
      return plots.filter(p => p.id === 'contrast_plot' || p.id === 'contrast_integral');
    }
    return plots;
  }, [plots, mode]);

  return (
    <div className="impulse-construction-viewer">
      <HeaderBanner metadata={metadata} />

      <PlotDisplay
        plots={filteredPlots}
        isLoading={false}
        emptyMessage="Adjust \u03b5 to explore the delta construction."
      />

      {mode === 'contrast' && <ContrastExplanation />}
    </div>
  );
}

export default ImpulseConstructionViewer;
