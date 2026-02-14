/**
 * FourierPhaseMagnitudeViewer Component
 *
 * Redesigned tabbed viewer for Fourier Phase vs Magnitude simulation.
 * Features:
 * - Tab-based navigation: Sources | Hybrid Analysis | Detailed Metrics
 * - Clean, decluttered interface
 * - Side-by-side source comparison as default view
 * - Audio playback with Web Audio API
 */

import React, { useState, useRef, useCallback, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/FourierPhaseMagnitudeViewer.css';

/**
 * Tab Bar Component
 */
const TabBar = memo(function TabBar({ activeTab, onTabChange, isImageMode }) {
  const tabs = [
    { id: 'sources', label: 'Sources', icon: '📊' },
    { id: 'hybrid', label: 'Hybrid Analysis', icon: '⚡' },
    { id: 'metrics', label: 'Detailed Metrics', icon: '📈' },
  ];

  return (
    <div className="tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
      <div className="tab-mode-indicator">
        <span className={`mode-pill ${isImageMode ? 'image' : 'audio'}`}>
          {isImageMode ? '🖼️ Image' : '🔊 Audio'}
        </span>
      </div>
    </div>
  );
});

/**
 * Audio Player Component with play/pause controls
 */
const AudioPlayer = memo(function AudioPlayer({ audioData, label, color, large }) {
  const audioRef = useRef(null);

  const handlePlay = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play();
    }
  }, []);

  const handlePause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
  }, []);

  if (!audioData) {
    return <div className="audio-player-placeholder">No audio data</div>;
  }

  return (
    <div className={`audio-player ${large ? 'large' : ''}`} style={{ borderColor: color }}>
      <div className="audio-label" style={{ color }}>{label}</div>
      <audio ref={audioRef} src={audioData} preload="auto" />
      <div className="audio-controls">
        <button className="audio-btn play" onClick={handlePlay} title="Play">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <polygon points="5,3 19,12 5,21" fill="currentColor" />
          </svg>
        </button>
        <button className="audio-btn pause" onClick={handlePause} title="Pause">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <rect x="6" y="4" width="4" height="16" fill="currentColor" />
            <rect x="14" y="4" width="4" height="16" fill="currentColor" />
          </svg>
        </button>
      </div>
    </div>
  );
});

/**
 * Image Display Card with label
 */
const ImageCard = memo(function ImageCard({ src, label, sublabel, borderColor, large }) {
  if (!src) {
    return (
      <div className={`image-card placeholder ${large ? 'large' : ''}`}>
        <div className="image-label">{label}</div>
        <div className="image-placeholder-text">No image data</div>
      </div>
    );
  }

  return (
    <div className={`image-card ${large ? 'large' : ''}`} style={{ borderColor: borderColor || 'transparent' }}>
      <div className="image-label" style={{ color: borderColor }}>{label}</div>
      {sublabel && <div className="image-sublabel">{sublabel}</div>}
      <img src={src} alt={label} className="fourier-image" />
    </div>
  );
});

/**
 * Compact Metrics Display
 */
const MetricsInline = memo(function MetricsInline({ metrics, type, color }) {
  if (!metrics) return null;

  return (
    <div className="metrics-inline" style={{ borderLeftColor: color }}>
      <span className="metric-item">
        <span className="metric-label">MSE:</span>
        <span className="metric-val">{metrics.mse?.toFixed(6) || '0'}</span>
      </span>
      <span className="metric-item">
        <span className="metric-label">Corr:</span>
        <span className="metric-val">{metrics.correlation?.toFixed(4) || '0'}</span>
      </span>
      {type === 'image' && (
        <span className="metric-item">
          <span className="metric-label">SSIM:</span>
          <span className="metric-val">{metrics.ssim?.toFixed(4) || '0'}</span>
        </span>
      )}
      {type === 'audio' && metrics.snr_db !== undefined && (
        <span className="metric-item">
          <span className="metric-label">SNR:</span>
          <span className="metric-val">{metrics.snr_db?.toFixed(1)} dB</span>
        </span>
      )}
    </div>
  );
});

/**
 * Mode Badge Component
 */
const ModeBadge = memo(function ModeBadge({ mode }) {
  if (!mode || mode === 'original') return null;

  const isUniformMag = mode === 'uniform_magnitude';
  const label = isUniformMag ? 'Uniform Magnitude' : 'Uniform Phase';
  const color = isUniformMag ? '#ef4444' : '#10b981';

  return (
    <span className="mode-badge-small" style={{ backgroundColor: `${color}20`, color, borderColor: `${color}40` }}>
      {label}
    </span>
  );
});

/**
 * Source Card Component - Shows original + reconstructed when mode applied
 */
const SourceCard = memo(function SourceCard({ source, sourceNum, color, type }) {
  const isImage = type === 'image';
  const hasMode = source?.mode && source.mode !== 'original';
  const colorName = sourceNum === 1 ? 'cyan' : 'coral';

  return (
    <div className="source-column">
      <div className={`source-header-card ${colorName}`}>
        <span className="source-badge">{sourceNum}</span>
        <span className="source-title">{source?.name || `Source ${sourceNum}`}</span>
        <ModeBadge mode={source?.mode} />
      </div>

      {isImage ? (
        <>
          {/* Original vs Reconstructed comparison when mode is applied */}
          {hasMode ? (
            <div className="mode-comparison">
              <div className="comparison-header">
                <span className="comparison-arrow">Original → Reconstructed</span>
                <span className="comparison-desc">
                  {source.mode === 'uniform_magnitude'
                    ? 'All frequencies have same magnitude'
                    : 'All frequencies have same phase'}
                </span>
              </div>
              <div className="comparison-images">
                <ImageCard
                  src={source?.original}
                  label="Original"
                  borderColor={color}
                />
                <div className="arrow-indicator">→</div>
                <ImageCard
                  src={source?.reconstructed}
                  label="Reconstructed"
                  sublabel={source.mode === 'uniform_magnitude' ? 'Uniform |F|' : 'Uniform ∠F'}
                  borderColor="#a78bfa"
                />
              </div>
            </div>
          ) : (
            <div className="source-main-image">
              <ImageCard
                src={source?.original}
                label="Original Image"
                borderColor={color}
                large
              />
            </div>
          )}

          {/* Fourier Spectra */}
          <div className="spectra-section">
            <div className="spectra-label">Fourier Transform</div>
            <div className="source-spectra">
              <ImageCard
                src={source?.magnitude}
                label="Magnitude |F(u,v)|"
                sublabel="Frequency amplitudes"
                borderColor="#ef4444"
              />
              <ImageCard
                src={source?.phase}
                label="Phase ∠F(u,v)"
                sublabel="Frequency timing"
                borderColor="#10b981"
              />
            </div>
          </div>
        </>
      ) : (
        <div className="source-audio">
          <AudioPlayer
            audioData={source?.audio}
            label={`Play ${source?.name || `Source ${sourceNum}`}`}
            color={color}
            large
          />
        </div>
      )}

      <MetricsInline metrics={source?.metrics} type={type} color={color} />
    </div>
  );
});

/**
 * Sources Tab - Side by side comparison
 */
const SourcesTab = memo(function SourcesTab({ source1, source2, type }) {
  return (
    <div className="sources-tab">
      {/* Intro Banner */}
      <div className="sources-intro">
        <div className="intro-icon">🔬</div>
        <div className="intro-text">
          <strong>Fourier Transform Decomposition:</strong> Every image can be broken into
          <span className="highlight-mag"> magnitude</span> (how much of each frequency) and
          <span className="highlight-phase"> phase</span> (where each frequency is aligned).
        </div>
      </div>

      <div className="sources-grid">
        <SourceCard source={source1} sourceNum={1} color="#22d3ee" type={type} />

        {/* Divider */}
        <div className="source-divider">
          <div className="divider-line"></div>
          <span className="divider-text">VS</span>
          <div className="divider-line"></div>
        </div>

        <SourceCard source={source2} sourceNum={2} color="#f87171" type={type} />
      </div>

      {/* CTA to Hybrid Tab */}
      <div className="sources-cta">
        <span className="cta-icon">👆</span>
        <span className="cta-text">Click <strong>"Hybrid Analysis"</strong> tab to see what happens when we swap magnitude and phase!</span>
      </div>
    </div>
  );
});

/**
 * Hybrid Analysis Tab - The "wow" demonstration
 */
const HybridTab = memo(function HybridTab({ hybrids, source1, source2, type }) {
  const isImage = type === 'image';
  const hybrid1 = hybrids?.mag1_phase2;
  const hybrid2 = hybrids?.mag2_phase1;

  return (
    <div className="hybrid-tab">
      {/* Big Insight Banner */}
      <div className="insight-banner-large">
        <div className="insight-icon">💡</div>
        <div className="insight-content">
          <h3 className="insight-title">Phase Carries Structure!</h3>
          <p className="insight-description">
            {isImage
              ? "When we swap magnitude and phase between images, the result LOOKS like whichever image provided the PHASE - not the magnitude!"
              : "Phase determines the temporal structure (waveform shape). Both magnitude and phase contribute to perception - magnitude affects frequency content while phase affects timing relationships."}
          </p>
        </div>
      </div>

      {/* Hybrid Results */}
      <div className="hybrid-results-grid">
        {/* Hybrid 1: Mag1 + Phase2 */}
        <div className="hybrid-result-card green">
          <div className="hybrid-formula-header">
            <span className="formula-part mag">Magnitude</span>
            <span className="formula-from">from {source1?.name || 'Source 1'}</span>
            <span className="formula-plus">+</span>
            <span className="formula-part phase">Phase</span>
            <span className="formula-from">from {source2?.name || 'Source 2'}</span>
          </div>

          <div className="hybrid-content">
            {isImage ? (
              <ImageCard
                src={hybrid1?.image}
                label=""
                borderColor="#34d399"
                large
              />
            ) : (
              <AudioPlayer
                audioData={hybrid1?.audio}
                label="Play Hybrid"
                color="#34d399"
                large
              />
            )}
          </div>

          <div className="hybrid-result-footer green">
            <span className="result-arrow">→</span>
            <span className="result-text">
              {isImage
                ? `Looks like ${source2?.name || 'Source 2'}!`
                : `Waveform shape from ${source2?.name || 'Source 2'}`}
            </span>
            <span className="result-corr">
              Correlation: {(hybrid1?.correlation_to_source || hybrid1?.correlation || 0).toFixed(4)}
            </span>
          </div>
        </div>

        {/* Swap Indicator */}
        <div className="swap-indicator-vertical">
          <svg viewBox="0 0 24 24" width="40" height="40">
            <path d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4"
                  stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
          </svg>
          <span>Swapped</span>
        </div>

        {/* Hybrid 2: Mag2 + Phase1 */}
        <div className="hybrid-result-card amber">
          <div className="hybrid-formula-header">
            <span className="formula-part mag">Magnitude</span>
            <span className="formula-from">from {source2?.name || 'Source 2'}</span>
            <span className="formula-plus">+</span>
            <span className="formula-part phase">Phase</span>
            <span className="formula-from">from {source1?.name || 'Source 1'}</span>
          </div>

          <div className="hybrid-content">
            {isImage ? (
              <ImageCard
                src={hybrid2?.image}
                label=""
                borderColor="#fbbf24"
                large
              />
            ) : (
              <AudioPlayer
                audioData={hybrid2?.audio}
                label="Play Hybrid"
                color="#fbbf24"
                large
              />
            )}
          </div>

          <div className="hybrid-result-footer amber">
            <span className="result-arrow">→</span>
            <span className="result-text">
              {isImage
                ? `Looks like ${source1?.name || 'Source 1'}!`
                : `Waveform shape from ${source1?.name || 'Source 1'}`}
            </span>
            <span className="result-corr">
              Correlation: {(hybrid2?.correlation_to_source || hybrid2?.correlation || 0).toFixed(4)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
});

/**
 * Detailed Metrics Tab - Comparison table
 */
const MetricsTab = memo(function MetricsTab({ source1, source2, hybrids, type }) {
  const isImage = type === 'image';
  const m1 = source1?.metrics || {};
  const m2 = source2?.metrics || {};
  const h1 = hybrids?.mag1_phase2 || {};
  const h2 = hybrids?.mag2_phase1 || {};

  return (
    <div className="metrics-tab">
      {/* Source Comparison Table */}
      <div className="metrics-section">
        <h3 className="metrics-section-title">
          <span className="section-icon">📊</span>
          Source Comparison
        </h3>
        <div className="metrics-table">
          <div className="metrics-table-header">
            <div className="metric-col header">Metric</div>
            <div className="metric-col source1">{source1?.name || 'Source 1'}</div>
            <div className="metric-col source2">{source2?.name || 'Source 2'}</div>
          </div>
          <div className="metrics-table-row">
            <div className="metric-col header">MSE</div>
            <div className="metric-col source1">{m1.mse?.toFixed(6) || '—'}</div>
            <div className="metric-col source2">{m2.mse?.toFixed(6) || '—'}</div>
          </div>
          <div className="metrics-table-row">
            <div className="metric-col header">Correlation</div>
            <div className="metric-col source1">{m1.correlation?.toFixed(4) || '—'}</div>
            <div className="metric-col source2">{m2.correlation?.toFixed(4) || '—'}</div>
          </div>
          {isImage && (
            <div className="metrics-table-row">
              <div className="metric-col header">SSIM</div>
              <div className="metric-col source1">{m1.ssim?.toFixed(4) || '—'}</div>
              <div className="metric-col source2">{m2.ssim?.toFixed(4) || '—'}</div>
            </div>
          )}
          {!isImage && (
            <div className="metrics-table-row">
              <div className="metric-col header">SNR (dB)</div>
              <div className="metric-col source1">{m1.snr_db?.toFixed(1) || '—'}</div>
              <div className="metric-col source2">{m2.snr_db?.toFixed(1) || '—'}</div>
            </div>
          )}
        </div>
      </div>

      {/* Hybrid Analysis Results */}
      <div className="metrics-section">
        <h3 className="metrics-section-title">
          <span className="section-icon">⚡</span>
          Hybrid Analysis Results
        </h3>
        <div className="hybrid-metrics-grid">
          <div className="hybrid-metric-card green">
            <div className="hybrid-metric-label">Mag₁ + Phase₂</div>
            <div className="hybrid-metric-result">
              Resembles: <strong>{source2?.name || 'Source 2'}</strong>
            </div>
            <div className="hybrid-metric-value">
              Correlation: {(h1.correlation_to_source || h1.correlation || 0).toFixed(4)}
            </div>
          </div>
          <div className="hybrid-metric-card amber">
            <div className="hybrid-metric-label">Mag₂ + Phase₁</div>
            <div className="hybrid-metric-result">
              Resembles: <strong>{source1?.name || 'Source 1'}</strong>
            </div>
            <div className="hybrid-metric-value">
              Correlation: {(h2.correlation_to_source || h2.correlation || 0).toFixed(4)}
            </div>
          </div>
        </div>
      </div>

      {/* Key Takeaway */}
      <div className="metrics-takeaway">
        <div className="takeaway-icon">🎓</div>
        <div className="takeaway-text">
          <strong>Key Insight:</strong> The hybrid results prove that phase information
          is more important than magnitude for preserving the structural characteristics
          of {isImage ? 'images' : 'audio signals'}. The reconstructed {isImage ? 'image' : 'signal'} inherits
          its recognizable features from whichever source provided the phase spectrum.
        </div>
      </div>
    </div>
  );
});

/**
 * Audio Waveform Plots using Plotly
 */
const AudioWaveformPlots = memo(function AudioWaveformPlots({ plots }) {
  if (!plots || plots.length === 0) return null;

  return (
    <div className="audio-waveforms-section">
      <h3 className="waveforms-title">Waveform Analysis</h3>
      <div className="waveforms-grid">
        {plots.map((plot, index) => (
          <div key={plot.id || index} className="waveform-card">
            <Plot
              data={plot.data}
              layout={{
                ...plot.layout,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
                font: { color: '#e2e8f0', size: 11 },
                margin: { l: 50, r: 20, t: 40, b: 40 },
                height: plot.layout?.height || 180,
                xaxis: {
                  ...plot.layout?.xaxis,
                  gridcolor: 'rgba(148, 163, 184, 0.15)',
                  zerolinecolor: 'rgba(148, 163, 184, 0.3)',
                },
                yaxis: {
                  ...plot.layout?.yaxis,
                  gridcolor: 'rgba(148, 163, 184, 0.15)',
                  zerolinecolor: 'rgba(148, 163, 184, 0.3)',
                },
              }}
              config={{
                responsive: true,
                displayModeBar: false,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        ))}
      </div>
    </div>
  );
});

/**
 * Main FourierPhaseMagnitudeViewer Component
 */
function FourierPhaseMagnitudeViewer({ metadata, plots }) {
  const [activeTab, setActiveTab] = useState('sources');

  if (!metadata?.visualization_data) {
    return (
      <div className="fourier-viewer-empty">
        <p>Loading Fourier Analysis visualization...</p>
      </div>
    );
  }

  const vizData = metadata.visualization_data;
  const isImageMode = vizData.type === 'image';

  return (
    <div className="fourier-phase-magnitude-viewer">
      {/* Tab Navigation */}
      <TabBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isImageMode={isImageMode}
      />

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'sources' && (
          <SourcesTab
            source1={vizData.source1}
            source2={vizData.source2}
            type={vizData.type}
          />
        )}

        {activeTab === 'hybrid' && (
          <HybridTab
            hybrids={vizData.hybrids}
            source1={vizData.source1}
            source2={vizData.source2}
            type={vizData.type}
          />
        )}

        {activeTab === 'metrics' && (
          <MetricsTab
            source1={vizData.source1}
            source2={vizData.source2}
            hybrids={vizData.hybrids}
            type={vizData.type}
          />
        )}
      </div>

      {/* Audio Waveform Plots (only for audio mode, shown below tabs) */}
      {!isImageMode && plots && plots.length > 0 && (
        <AudioWaveformPlots plots={plots} />
      )}
    </div>
  );
}

export default memo(FourierPhaseMagnitudeViewer);
