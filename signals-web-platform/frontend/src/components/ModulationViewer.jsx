/**
 * ModulationViewer Component
 *
 * Custom viewer for Modulation Techniques simulation matching PyQt5 version.
 * Features three demo modes: AM, FM/PM, FDM with audio playback.
 */

import React, { useState, useCallback, useRef, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import './ModulationViewer.css';

/**
 * Tab navigation bar
 */
const TABS = [
  { id: 'am', label: 'Amplitude Modulation', icon: '📻', color: '#2563EB' },
  { id: 'fm_pm', label: 'Frequency & Phase', icon: '📡', color: '#16A34A' },
  { id: 'fdm', label: 'Freq Division Mux', icon: '📶', color: '#CA8A04' },
];

const TabBar = memo(function TabBar({ activeTab, onTabChange }) {
  return (
    <div className="modulation-tab-bar">
      {TABS.map(tab => (
        <button
          key={tab.id}
          className={`modulation-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
          style={{ '--tab-color': tab.color }}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  );
});

/**
 * Audio Player component with play/pause controls
 */
const AudioPlayer = memo(function AudioPlayer({ audioData, label, color }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Reload audio when data changes
  useEffect(() => {
    if (audioRef.current && audioData) {
      // Stop current playback
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      // Load new audio data
      audioRef.current.load();
    }
  }, [audioData]);

  const handlePlay = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }, []);

  const handlePause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
  }, []);

  if (!audioData) {
    return <div className="audio-player-placeholder">No audio</div>;
  }

  return (
    <div className="modulation-audio-player" style={{ borderColor: color }}>
      <audio
        ref={audioRef}
        src={audioData}
        preload="auto"
        onEnded={handleEnded}
      />
      <button
        className={`audio-play-btn ${isPlaying ? 'playing' : ''}`}
        onClick={isPlaying ? handlePause : handlePlay}
        style={{ backgroundColor: color }}
      >
        {isPlaying ? (
          <svg viewBox="0 0 24 24" width="20" height="20">
            <rect x="6" y="4" width="4" height="16" fill="currentColor" />
            <rect x="14" y="4" width="4" height="16" fill="currentColor" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="20" height="20">
            <polygon points="5,3 19,12 5,21" fill="currentColor" />
          </svg>
        )}
      </button>
      <span className="audio-label">{label}</span>
    </div>
  );
});

/**
 * Audio Controls Panel
 */
const AudioControls = memo(function AudioControls({ audioData, demoMode }) {
  if (!audioData) return null;

  if (demoMode === 'am' || demoMode === 'fm_pm') {
    return (
      <div className="audio-controls-panel">
        <h4 className="audio-title">Audio Playback</h4>
        <div className="audio-buttons-row">
          <AudioPlayer
            audioData={audioData.original}
            label="Original"
            color="#16A34A"
          />
          <AudioPlayer
            audioData={audioData.modulated}
            label="Modulated"
            color="#CA8A04"
          />
          <AudioPlayer
            audioData={audioData.recovered}
            label="Recovered"
            color="#2563EB"
          />
        </div>
      </div>
    );
  } else if (demoMode === 'fdm') {
    return (
      <div className="audio-controls-panel">
        <h4 className="audio-title">Audio Playback</h4>
        <div className="audio-buttons-row">
          <AudioPlayer
            audioData={audioData.multiplexed}
            label="Multiplexed"
            color="#CA8A04"
          />
          <AudioPlayer
            audioData={audioData.demodulated}
            label="Demodulated"
            color="#2563EB"
          />
        </div>
      </div>
    );
  }

  return null;
});

/**
 * Waveform Plots Display - vertical layout matching PyQt5
 */
const WaveformPlots = memo(function WaveformPlots({ plots }) {
  if (!plots || plots.length === 0) return null;

  return (
    <div className="modulation-plots-section">
      <div className="plots-grid">
        {plots.map((plot, index) => (
          <div key={plot.id || index} className="plot-card">
            <Plot
              data={plot.data}
              layout={{
                ...plot.layout,
                title: {
                  text: plot.title,
                  font: { size: 14, color: '#e2e8f0', family: 'system-ui, sans-serif' },
                  x: 0.5,
                  xanchor: 'center',
                },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(15, 23, 42, 0.6)',
                font: { color: '#e2e8f0', size: 12 },
                margin: { l: 60, r: 25, t: 40, b: 50 },
                height: 180,
                xaxis: {
                  ...plot.layout?.xaxis,
                  title: {
                    text: plot.layout?.xaxis?.title || 'Time (s)',
                    font: { size: 12, color: '#94a3b8' },
                    standoff: 10,
                  },
                  gridcolor: 'rgba(148, 163, 184, 0.2)',
                  zerolinecolor: 'rgba(148, 163, 184, 0.4)',
                  tickfont: { size: 10, color: '#94a3b8' },
                  showgrid: true,
                  showline: true,
                  linecolor: 'rgba(148, 163, 184, 0.3)',
                },
                yaxis: {
                  ...plot.layout?.yaxis,
                  title: {
                    text: plot.layout?.yaxis?.title || 'Amplitude',
                    font: { size: 12, color: '#94a3b8' },
                    standoff: 5,
                  },
                  gridcolor: 'rgba(148, 163, 184, 0.2)',
                  zerolinecolor: 'rgba(148, 163, 184, 0.4)',
                  tickfont: { size: 10, color: '#94a3b8' },
                  showgrid: true,
                  showline: true,
                  linecolor: 'rgba(148, 163, 184, 0.3)',
                },
                shapes: plot.layout?.shapes,
                showlegend: false,
              }}
              config={{
                responsive: true,
                displayModeBar: false,
              }}
              style={{ width: '100%', height: '180px' }}
            />
          </div>
        ))}
      </div>
    </div>
  );
});

/**
 * AM Demo Content
 */
const AMDemoContent = memo(function AMDemoContent({ plots, audioData }) {
  return (
    <div className="demo-content am-content">
      <div className="demo-layout">
        <div className="plots-area">
          <WaveformPlots plots={plots} />
        </div>
        <div className="side-panel">
          <AudioControls audioData={audioData} demoMode="am" />
        </div>
      </div>
    </div>
  );
});

/**
 * FM/PM Demo Content
 */
const FMPMDemoContent = memo(function FMPMDemoContent({ plots, audioData }) {
  return (
    <div className="demo-content fm-content">
      <div className="demo-layout">
        <div className="plots-area">
          <WaveformPlots plots={plots} />
        </div>
        <div className="side-panel">
          <AudioControls audioData={audioData} demoMode="fm_pm" />
        </div>
      </div>
    </div>
  );
});

/**
 * FDM Demo Content
 */
const FDMDemoContent = memo(function FDMDemoContent({ plots, audioData }) {
  return (
    <div className="demo-content fdm-content">
      <div className="demo-layout">
        <div className="plots-area">
          <WaveformPlots plots={plots} />
        </div>
        <div className="side-panel">
          <AudioControls audioData={audioData} demoMode="fdm" />
        </div>
      </div>
    </div>
  );
});

/**
 * Main ModulationViewer Component
 */
function ModulationViewer({ metadata, plots, currentParams, onParamChange }) {
  // Prioritize currentParams since it's updated immediately on user interaction,
  // while metadata only updates after API response (fixes glitch when adjusting sliders)
  const demoMode = currentParams?.demo_mode || metadata?.demo_mode || 'am';
  const audioData = metadata?.audio_data;

  // Handle tab change by updating the demo_mode parameter
  const handleTabChange = useCallback((newMode) => {
    if (onParamChange) {
      onParamChange('demo_mode', newMode);
    }
  }, [onParamChange]);

  if (!metadata) {
    return (
      <div className="modulation-viewer-empty">
        <p>Loading Modulation simulation...</p>
      </div>
    );
  }

  return (
    <div className="modulation-viewer">
      {/* Tab Navigation */}
      <TabBar activeTab={demoMode} onTabChange={handleTabChange} />

      {/* Tab Content */}
      <div className="tab-content">
        {demoMode === 'am' && (
          <AMDemoContent plots={plots} audioData={audioData} />
        )}
        {demoMode === 'fm_pm' && (
          <FMPMDemoContent plots={plots} audioData={audioData} />
        )}
        {demoMode === 'fdm' && (
          <FDMDemoContent plots={plots} audioData={audioData} />
        )}
      </div>
    </div>
  );
}

export default ModulationViewer;
