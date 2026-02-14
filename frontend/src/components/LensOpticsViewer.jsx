/**
 * LensOpticsViewer Component
 *
 * Tabbed viewer for Lens Optics simulation matching PyQt5 version.
 * Features:
 * - Tab-based navigation: Images | PSF Analysis | Metrics
 * - Side-by-side original/blurred image comparison
 * - PSF visualization with cross-section and encircled energy
 * - Comprehensive lens, PSF, and quality metrics
 */

import React, { useState, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/LensOpticsViewer.css';

/**
 * Tab Bar Component
 */
const TabBar = memo(function TabBar({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'images', label: 'Images', icon: '🖼️' },
    { id: 'psf', label: 'PSF Analysis', icon: '🎯' },
    { id: 'metrics', label: 'Quality Metrics', icon: '📊' },
  ];

  return (
    <div className="lens-tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`lens-tab-button ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="lens-tab-icon">{tab.icon}</span>
          <span className="lens-tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  );
});

/**
 * Image Card - displays base64 image with label
 */
const ImageCard = memo(function ImageCard({ src, label, sublabel, borderColor, large }) {
  if (!src) {
    return (
      <div className={`lens-image-card placeholder ${large ? 'large' : ''}`}>
        <div className="lens-image-label">{label}</div>
        <div className="lens-image-placeholder">No image data</div>
      </div>
    );
  }

  return (
    <div className={`lens-image-card ${large ? 'large' : ''}`} style={{ borderColor: borderColor || 'transparent' }}>
      <div className="lens-image-label" style={{ color: borderColor }}>{label}</div>
      {sublabel && <div className="lens-image-sublabel">{sublabel}</div>}
      <img src={src} alt={label} className="lens-image" />
    </div>
  );
});

/**
 * Metric Row - single metric display
 */
const MetricRow = memo(function MetricRow({ label, value, unit, color }) {
  return (
    <div className="lens-metric-row">
      <span className="lens-metric-label">{label}</span>
      <span className="lens-metric-value" style={{ color: color || '#e2e8f0' }}>
        {value}{unit && <span className="lens-metric-unit"> {unit}</span>}
      </span>
    </div>
  );
});

/**
 * Metric Card - group of metrics
 */
const MetricCard = memo(function MetricCard({ title, icon, children, color }) {
  return (
    <div className="lens-metric-card" style={{ borderLeftColor: color }}>
      <div className="lens-metric-card-header">
        <span className="lens-metric-card-icon">{icon}</span>
        <span className="lens-metric-card-title">{title}</span>
      </div>
      <div className="lens-metric-card-content">
        {children}
      </div>
    </div>
  );
});

/**
 * Images Tab - Original vs Blurred comparison
 */
const ImagesTab = memo(function ImagesTab({ metadata, plots }) {
  const images = metadata?.images || {};
  const lensInfo = metadata?.lens_info || {};
  const qualityAssessment = metadata?.quality_assessment || '';
  const testPattern = metadata?.test_pattern || '';
  const atmosphereEnabled = metadata?.atmosphere_enabled;
  const seeingArcsec = metadata?.seeing_arcsec;

  // Get original and blurred plots for Plotly rendering
  const originalPlot = plots?.find(p => p.id === 'original_image');
  const blurredPlot = plots?.find(p => p.id === 'blurred_image');

  return (
    <div className="lens-images-tab">
      {/* Status Banner */}
      <div className="lens-status-banner">
        <div className="lens-status-item">
          <span className="lens-status-label">Pattern:</span>
          <span className="lens-status-value">{testPattern}</span>
        </div>
        <div className="lens-status-item">
          <span className="lens-status-label">f/</span>
          <span className="lens-status-value">{lensInfo.f_number || '—'}</span>
        </div>
        <div className="lens-status-item">
          <span className="lens-status-label">Airy:</span>
          <span className="lens-status-value">{lensInfo.airy_radius_um || '—'} um</span>
        </div>
        {atmosphereEnabled && (
          <div className="lens-status-item seeing">
            <span className="lens-status-label">Seeing:</span>
            <span className="lens-status-value">{seeingArcsec} arcsec</span>
          </div>
        )}
        <div className={`lens-quality-badge ${qualityAssessment.includes('Excellent') ? 'excellent' : qualityAssessment.includes('Good') ? 'good' : 'moderate'}`}>
          {qualityAssessment}
        </div>
      </div>

      {/* Side-by-side Image Comparison */}
      <div className="lens-images-grid">
        {/* Original Image */}
        <div className="lens-image-panel">
          <div className="lens-image-header original">
            <span className="lens-image-title">Original Image</span>
          </div>
          {originalPlot ? (
            <div className="lens-plotly-container">
              <Plot
                data={originalPlot.data}
                layout={{
                  ...originalPlot.layout,
                  autosize: true,
                  height: 350,
                  font: { color: '#e2e8f0' },
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          ) : (
            <ImageCard src={images.original} label="" borderColor="#00A0FF" large />
          )}
        </div>

        {/* Arrow Indicator */}
        <div className="lens-transform-arrow">
          <div className="lens-arrow-icon">→</div>
          <div className="lens-arrow-label">PSF Conv.</div>
        </div>

        {/* Blurred Image */}
        <div className="lens-image-panel">
          <div className="lens-image-header blurred">
            <span className="lens-image-title">Blurred Image</span>
            <span className="lens-image-fnumber">f/{lensInfo.f_number || '—'}</span>
          </div>
          {blurredPlot ? (
            <div className="lens-plotly-container">
              <Plot
                data={blurredPlot.data}
                layout={{
                  ...blurredPlot.layout,
                  autosize: true,
                  height: 350,
                  font: { color: '#e2e8f0' },
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          ) : (
            <ImageCard src={images.blurred} label="" borderColor="#FF5733" large />
          )}
        </div>
      </div>

      {/* Quick Metrics Row */}
      <div className="lens-quick-metrics">
        <div className="lens-quick-metric">
          <span className="lens-quick-label">SSIM</span>
          <span className="lens-quick-value">{metadata?.quality_metrics?.ssim || '—'}</span>
        </div>
        <div className="lens-quick-metric">
          <span className="lens-quick-label">PSNR</span>
          <span className="lens-quick-value">{metadata?.quality_metrics?.psnr || '—'} dB</span>
        </div>
        <div className="lens-quick-metric">
          <span className="lens-quick-label">Contrast Loss</span>
          <span className="lens-quick-value">{metadata?.quality_metrics?.contrast_reduction || '—'}%</span>
        </div>
        <div className="lens-quick-metric">
          <span className="lens-quick-label">Edge Preservation</span>
          <span className="lens-quick-value">{metadata?.quality_metrics?.edge_preservation || '—'}</span>
        </div>
      </div>
    </div>
  );
});

/**
 * PSF Analysis Tab - PSF visualization, cross-section, encircled energy
 */
const PSFTab = memo(function PSFTab({ metadata, plots }) {
  const psfMetrics = metadata?.psf_metrics || {};
  const lensInfo = metadata?.lens_info || {};

  const psfPlot = plots?.find(p => p.id === 'psf');
  const crossSectionPlot = plots?.find(p => p.id === 'cross_section');
  const encircledEnergyPlot = plots?.find(p => p.id === 'encircled_energy');

  return (
    <div className="lens-psf-tab">
      {/* PSF Metrics Banner */}
      <div className="lens-psf-banner">
        <div className="lens-psf-metric">
          <span className="lens-psf-metric-label">FWHM</span>
          <span className="lens-psf-metric-value">{psfMetrics.fwhm_um || '—'} um</span>
        </div>
        <div className="lens-psf-metric">
          <span className="lens-psf-metric-label">EE50</span>
          <span className="lens-psf-metric-value">{psfMetrics.ee50_um || '—'} um</span>
        </div>
        <div className="lens-psf-metric">
          <span className="lens-psf-metric-label">EE80</span>
          <span className="lens-psf-metric-value">{psfMetrics.ee80_um || '—'} um</span>
        </div>
        <div className="lens-psf-metric">
          <span className="lens-psf-metric-label">Airy Radius</span>
          <span className="lens-psf-metric-value">{lensInfo.airy_radius_um || '—'} um</span>
        </div>
        <div className="lens-psf-metric">
          <span className="lens-psf-metric-label">Strehl</span>
          <span className="lens-psf-metric-value">{psfMetrics.strehl_ratio || '—'}</span>
        </div>
      </div>

      {/* PSF Plots Grid */}
      <div className="lens-psf-plots-grid">
        {/* PSF Image (log scale) */}
        <div className="lens-psf-plot-panel">
          <div className="lens-plot-title">Point Spread Function (Log Scale)</div>
          {psfPlot && (
            <Plot
              data={psfPlot.data}
              layout={{
                ...psfPlot.layout,
                autosize: true,
                height: 300,
                font: { color: '#e2e8f0', size: 10 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          )}
        </div>

        {/* Cross Section */}
        <div className="lens-psf-plot-panel">
          <div className="lens-plot-title">PSF Cross-Section</div>
          {crossSectionPlot && (
            <Plot
              data={crossSectionPlot.data}
              layout={{
                ...crossSectionPlot.layout,
                autosize: true,
                height: 300,
                font: { color: '#e2e8f0', size: 10 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          )}
        </div>

        {/* Encircled Energy */}
        <div className="lens-psf-plot-panel wide">
          <div className="lens-plot-title">Encircled Energy</div>
          {encircledEnergyPlot && (
            <Plot
              data={encircledEnergyPlot.data}
              layout={{
                ...encircledEnergyPlot.layout,
                autosize: true,
                height: 280,
                font: { color: '#e2e8f0', size: 10 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          )}
        </div>
      </div>
    </div>
  );
});

/**
 * Metrics Tab - Comprehensive metrics and MTF
 */
const MetricsTab = memo(function MetricsTab({ metadata, plots }) {
  const lensInfo = metadata?.lens_info || {};
  const psfMetrics = metadata?.psf_metrics || {};
  const qualityMetrics = metadata?.quality_metrics || {};

  const mtfPlot = plots?.find(p => p.id === 'mtf');

  return (
    <div className="lens-metrics-tab">
      {/* Metrics Cards Grid */}
      <div className="lens-metrics-grid">
        {/* Lens Parameters */}
        <MetricCard title="Lens Parameters" icon="🔭" color="#3b82f6">
          <MetricRow label="Aperture" value={lensInfo.diameter_mm} unit="mm" />
          <MetricRow label="Focal Length" value={lensInfo.focal_length_mm} unit="mm" />
          <MetricRow label="Wavelength" value={lensInfo.wavelength_nm} unit="nm" />
          <MetricRow label="f-number" value={`f/${lensInfo.f_number}`} color="#22d3ee" />
          <MetricRow label="Numerical Aperture" value={lensInfo.numerical_aperture} />
          <MetricRow label="Rayleigh Limit" value={lensInfo.rayleigh_limit_arcsec} unit="arcsec" />
        </MetricCard>

        {/* PSF Metrics */}
        <MetricCard title="PSF Metrics" icon="🎯" color="#a855f7">
          <MetricRow label="FWHM" value={psfMetrics.fwhm_um} unit="um" color="#22c55e" />
          <MetricRow label="Airy Radius" value={lensInfo.airy_radius_um} unit="um" color="#f59e0b" />
          <MetricRow label="EE50 Radius" value={psfMetrics.ee50_um} unit="um" />
          <MetricRow label="EE80 Radius" value={psfMetrics.ee80_um} unit="um" />
          <MetricRow label="Peak Intensity" value={psfMetrics.peak_intensity} />
          <MetricRow label="Strehl Ratio" value={psfMetrics.strehl_ratio} color="#22d3ee" />
        </MetricCard>

        {/* Image Quality */}
        <MetricCard title="Image Quality" icon="📈" color="#22c55e">
          <MetricRow label="SSIM" value={qualityMetrics.ssim} color="#22c55e" />
          <MetricRow label="PSNR" value={qualityMetrics.psnr} unit="dB" />
          <MetricRow label="MSE" value={qualityMetrics.mse} />
          <MetricRow label="Contrast Reduction" value={qualityMetrics.contrast_reduction} unit="%" color="#f59e0b" />
          <MetricRow label="Edge Preservation" value={qualityMetrics.edge_preservation} />
        </MetricCard>
      </div>

      {/* MTF Plot */}
      <div className="lens-mtf-section">
        <div className="lens-mtf-header">
          <span className="lens-mtf-title">Modulation Transfer Function (MTF)</span>
          <span className="lens-mtf-description">Spatial frequency response - higher is sharper</span>
        </div>
        {mtfPlot && (
          <div className="lens-mtf-plot">
            <Plot
              data={mtfPlot.data}
              layout={{
                ...mtfPlot.layout,
                autosize: true,
                height: 280,
                font: { color: '#e2e8f0', size: 11 },
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
      </div>

      {/* Quality Assessment */}
      <div className="lens-assessment-banner">
        <span className="lens-assessment-icon">
          {metadata?.quality_assessment?.includes('Excellent') ? '🌟' :
           metadata?.quality_assessment?.includes('Good') ? '✓' : '⚠️'}
        </span>
        <span className="lens-assessment-text">{metadata?.quality_assessment}</span>
      </div>
    </div>
  );
});

/**
 * Main LensOpticsViewer Component
 */
function LensOpticsViewer({ metadata, plots }) {
  const [activeTab, setActiveTab] = useState('images');

  if (!metadata) {
    return (
      <div className="lens-viewer-empty">
        <p>Loading Lens Optics visualization...</p>
      </div>
    );
  }

  return (
    <div className="lens-optics-viewer">
      {/* Tab Navigation */}
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab Content */}
      <div className="lens-tab-content">
        {activeTab === 'images' && (
          <ImagesTab metadata={metadata} plots={plots} />
        )}

        {activeTab === 'psf' && (
          <PSFTab metadata={metadata} plots={plots} />
        )}

        {activeTab === 'metrics' && (
          <MetricsTab metadata={metadata} plots={plots} />
        )}
      </div>
    </div>
  );
}

export default memo(LensOpticsViewer);
