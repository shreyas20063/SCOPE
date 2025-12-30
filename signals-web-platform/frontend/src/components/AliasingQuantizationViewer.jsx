/**
 * AliasingQuantizationViewer Component
 *
 * Tabbed viewer for Aliasing & Quantization simulation matching PyQt5 version.
 * Features 3 demo modes:
 * - Audio Aliasing: Downsampling with optional anti-aliasing filter
 * - Audio Quantization: Standard, Dither, Robert's method comparison
 * - Image Quantization: Visual comparison of quantization methods
 */

import React, { useState, useRef, useEffect, memo } from 'react';
import Plot from 'react-plotly.js';
import '../styles/AliasingQuantizationViewer.css';

/**
 * Tab Bar Component
 */
const TabBar = memo(function TabBar({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'aliasing', label: 'Audio Aliasing', icon: '🎵' },
    { id: 'quantization', label: 'Audio Quantization', icon: '📊' },
    { id: 'image', label: 'Image Quantization', icon: '🖼️' },
  ];

  return (
    <div className="aq-tab-bar">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`aq-tab-button ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="aq-tab-icon">{tab.icon}</span>
          <span className="aq-tab-label">{tab.label}</span>
        </button>
      ))}
    </div>
  );
});

/**
 * Audio Playback Controls
 */
const AudioControls = memo(function AudioControls({ metadata, labels }) {
  const [playingType, setPlayingType] = useState(null);
  const audioContextRef = useRef(null);
  const sourceNodeRef = useRef(null);

  const stopAudio = () => {
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop();
      } catch (e) { /* ignore */ }
      sourceNodeRef.current = null;
    }
    setPlayingType(null);
  };

  const playAudio = async (audioData, type) => {
    stopAudio();

    if (!audioData?.data || audioData.data.length === 0) return;

    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }

      const ctx = audioContextRef.current;
      if (ctx.state === 'suspended') await ctx.resume();

      let sampleRate = audioData.sample_rate || 44100;
      let data = audioData.data;

      // Web Audio API requires sample rate >= 8000 Hz
      // If sample rate is too low, upsample for playback
      const MIN_SAMPLE_RATE = 8000;
      if (sampleRate < MIN_SAMPLE_RATE) {
        const upsampleFactor = Math.ceil(MIN_SAMPLE_RATE / sampleRate);
        const newLength = data.length * upsampleFactor;
        const upsampled = new Float32Array(newLength);

        // Simple linear interpolation upsampling
        for (let i = 0; i < newLength; i++) {
          const srcIdx = i / upsampleFactor;
          const srcIdxFloor = Math.floor(srcIdx);
          const srcIdxCeil = Math.min(srcIdxFloor + 1, data.length - 1);
          const frac = srcIdx - srcIdxFloor;
          upsampled[i] = data[srcIdxFloor] * (1 - frac) + data[srcIdxCeil] * frac;
        }

        data = upsampled;
        sampleRate = sampleRate * upsampleFactor;
      }

      const buffer = ctx.createBuffer(1, data.length, sampleRate);
      const channelData = buffer.getChannelData(0);

      for (let i = 0; i < data.length; i++) {
        channelData[i] = data[i];
      }

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.onended = () => setPlayingType(null);
      source.start(0);

      sourceNodeRef.current = source;
      setPlayingType(type);
    } catch (err) {
      console.error('Audio playback error:', err);
      setPlayingType(null);
    }
  };

  useEffect(() => {
    return () => stopAudio();
  }, []);

  return (
    <div className="aq-audio-controls">
      <button
        className={`aq-audio-btn original ${playingType === 'original' ? 'playing' : ''}`}
        onClick={() => playingType === 'original' ? stopAudio() : playAudio(metadata?.audio_original, 'original')}
      >
        {playingType === 'original' ? '■' : '▶'} {labels?.original || 'Original'}
      </button>
      <button
        className={`aq-audio-btn processed ${playingType === 'processed' ? 'playing' : ''}`}
        onClick={() => playingType === 'processed' ? stopAudio() : playAudio(metadata?.audio_processed, 'processed')}
      >
        {playingType === 'processed' ? '■' : '▶'} {labels?.processed || 'Processed'}
      </button>
    </div>
  );
});

/**
 * Aliasing Demo Tab
 */
const AliasingTab = memo(function AliasingTab({ metadata, plots }) {
  const originalPlot = plots?.find(p => p.id === 'original_signal');
  const downsampledPlot = plots?.find(p => p.id === 'downsampled_signal');
  const spectrumPlot = plots?.find(p => p.id === 'frequency_spectrum');

  const factor = metadata?.downsample_factor || 4;
  const aaEnabled = metadata?.anti_aliasing;
  const nyquistOrig = metadata?.nyquist_original || 22050;
  const nyquistNew = metadata?.nyquist_new || 5512;
  const aliasingRisk = metadata?.aliasing_risk;

  return (
    <div className="aq-aliasing-tab">
      {/* Status Banner */}
      <div className="aq-status-banner">
        <div className="aq-status-item">
          <span className="aq-status-label">Factor:</span>
          <span className="aq-status-value">{factor}x</span>
        </div>
        <div className="aq-status-item">
          <span className="aq-status-label">Original SR:</span>
          <span className="aq-status-value">{metadata?.original_sr?.toLocaleString()} Hz</span>
        </div>
        <div className="aq-status-item">
          <span className="aq-status-label">New SR:</span>
          <span className="aq-status-value">{metadata?.new_sr?.toLocaleString()} Hz</span>
        </div>
        <div className="aq-status-item">
          <span className="aq-status-label">Anti-Aliasing:</span>
          <span className={`aq-status-value ${aaEnabled ? 'on' : 'off'}`}>
            {aaEnabled ? 'ON' : 'OFF'}
          </span>
        </div>
        <div className={`aq-aliasing-badge ${aliasingRisk ? 'warning' : 'safe'}`}>
          {aliasingRisk ? '⚠️ Aliasing Risk' : '✓ Safe'}
        </div>
      </div>

      {/* Audio Playback */}
      <AudioControls
        metadata={metadata}
        labels={{ original: 'Play Original', processed: 'Play Downsampled' }}
      />

      {/* Plots */}
      <div className="aq-plots-grid aliasing">
        {originalPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={originalPlot.data}
              layout={{ ...originalPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {downsampledPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={downsampledPlot.data}
              layout={{ ...downsampledPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {spectrumPlot && (
          <div className="aq-plot-panel wide">
            <Plot
              data={spectrumPlot.data}
              layout={{ ...spectrumPlot.layout, autosize: true, height: 250 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
      </div>

      {/* Nyquist Info */}
      <div className="aq-nyquist-info">
        <div className="aq-nyquist-item original">
          <span className="aq-nyquist-label">Original Nyquist:</span>
          <span className="aq-nyquist-value">{nyquistOrig.toLocaleString()} Hz</span>
        </div>
        <div className="aq-nyquist-item new">
          <span className="aq-nyquist-label">New Nyquist:</span>
          <span className="aq-nyquist-value">{nyquistNew.toLocaleString()} Hz</span>
        </div>
      </div>
    </div>
  );
});

/**
 * Quantization Demo Tab
 */
const QuantizationTab = memo(function QuantizationTab({ metadata, plots }) {
  const originalPlot = plots?.find(p => p.id === 'original_audio');
  const quantizedPlot = plots?.find(p => p.id === 'quantized_audio');
  const errorPlot = plots?.find(p => p.id === 'error_spectrum');
  const funcPlot = plots?.find(p => p.id === 'quant_function');

  const bits = metadata?.bit_depth || 4;
  const levels = metadata?.levels || 16;
  const method = metadata?.method || 'standard';
  const snrText = metadata?.snr_text || '—';

  const methodLabels = {
    standard: 'Standard Q',
    dither: 'With Dither',
    roberts: "Robert's"
  };

  return (
    <div className="aq-quantization-tab">
      {/* Status Banner */}
      <div className="aq-status-banner">
        <div className="aq-status-item">
          <span className="aq-status-label">Bit Depth:</span>
          <span className="aq-status-value">{bits} bits</span>
        </div>
        <div className="aq-status-item">
          <span className="aq-status-label">Levels:</span>
          <span className="aq-status-value">{levels}</span>
        </div>
        <div className="aq-status-item">
          <span className="aq-status-label">Method:</span>
          <span className="aq-status-value highlight">{methodLabels[method]}</span>
        </div>
        <div className="aq-snr-badge">
          SNR: {snrText}
        </div>
      </div>

      {/* Audio Playback */}
      <AudioControls
        metadata={metadata}
        labels={{ original: 'Play Original', processed: 'Play Quantized' }}
      />

      {/* Plots - 2x2 grid like PyQt5 */}
      <div className="aq-plots-grid quantization">
        {originalPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={originalPlot.data}
              layout={{ ...originalPlot.layout, autosize: true, height: 180 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {quantizedPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={quantizedPlot.data}
              layout={{ ...quantizedPlot.layout, autosize: true, height: 180 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {errorPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={errorPlot.data}
              layout={{ ...errorPlot.layout, autosize: true, height: 180 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {funcPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={funcPlot.data}
              layout={{ ...funcPlot.layout, autosize: true, height: 180 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
      </div>
    </div>
  );
});

/**
 * Image Quantization Demo Tab
 */
const ImageTab = memo(function ImageTab({ metadata, plots }) {
  const originalPlot = plots?.find(p => p.id === 'original_image');
  const standardPlot = plots?.find(p => p.id === 'standard_image');
  const ditherPlot = plots?.find(p => p.id === 'dither_image');
  const robertsPlot = plots?.find(p => p.id === 'roberts_image');
  const msePlot = plots?.find(p => p.id === 'mse_comparison');
  const histPlot = plots?.find(p => p.id === 'histograms');

  const bits = metadata?.bit_depth || 3;
  const levels = metadata?.levels || 8;

  return (
    <div className="aq-image-tab">
      {/* Status Banner */}
      <div className="aq-status-banner">
        <div className="aq-status-item">
          <span className="aq-status-label">Bit Depth:</span>
          <span className="aq-status-value">{bits} bits</span>
        </div>
        <div className="aq-status-item">
          <span className="aq-status-label">Levels:</span>
          <span className="aq-status-value">{levels}</span>
        </div>
        <div className="aq-mse-badges">
          <span className="aq-mse-badge standard">
            Standard: {metadata?.mse_standard?.toFixed(6) || '—'}
          </span>
          <span className="aq-mse-badge dither">
            Dither: {metadata?.mse_dither?.toFixed(6) || '—'}
          </span>
          <span className="aq-mse-badge roberts">
            Robert's: {metadata?.mse_roberts?.toFixed(6) || '—'}
          </span>
        </div>
      </div>

      {/* Image Grid - 2x2 like PyQt5 */}
      <div className="aq-image-grid">
        {originalPlot && (
          <div className="aq-image-panel">
            <div className="aq-image-title">Original (8-bit)</div>
            <Plot
              data={originalPlot.data}
              layout={{ ...originalPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {standardPlot && (
          <div className="aq-image-panel standard">
            <div className="aq-image-title">Standard Q ({bits} bits)</div>
            <Plot
              data={standardPlot.data}
              layout={{ ...standardPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {ditherPlot && (
          <div className="aq-image-panel dither">
            <div className="aq-image-title">Dither ({bits} bits)</div>
            <Plot
              data={ditherPlot.data}
              layout={{ ...ditherPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {robertsPlot && (
          <div className="aq-image-panel roberts">
            <div className="aq-image-title">Robert's ({bits} bits)</div>
            <Plot
              data={robertsPlot.data}
              layout={{ ...robertsPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
      </div>

      {/* Analysis Plots */}
      <div className="aq-analysis-grid">
        {msePlot && (
          <div className="aq-plot-panel">
            <Plot
              data={msePlot.data}
              layout={{ ...msePlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
        {histPlot && (
          <div className="aq-plot-panel">
            <Plot
              data={histPlot.data}
              layout={{ ...histPlot.layout, autosize: true, height: 200 }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        )}
      </div>
    </div>
  );
});

/**
 * Loading Spinner Component
 */
const LoadingSpinner = memo(function LoadingSpinner({ message }) {
  return (
    <div className="aq-loading">
      <div className="aq-loading-spinner"></div>
      <p>{message || 'Loading...'}</p>
    </div>
  );
});

/**
 * Main AliasingQuantizationViewer Component
 */
function AliasingQuantizationViewer({ metadata, plots, currentParams, onParamChange }) {
  const [activeTab, setActiveTab] = useState(metadata?.demo_mode || 'aliasing');
  const [isLoading, setIsLoading] = useState(false);

  // Sync tab with demo_mode parameter and detect loading state
  useEffect(() => {
    if (metadata?.demo_mode && metadata.demo_mode !== activeTab) {
      setActiveTab(metadata.demo_mode);
      setIsLoading(false);
    }
  }, [metadata?.demo_mode]);

  // Handle tab change - also update the parameter
  const handleTabChange = (tab) => {
    if (tab !== activeTab) {
      setIsLoading(true);
      setActiveTab(tab);
      if (onParamChange) {
        onParamChange('demo_mode', tab);
      }
    }
  };

  // Check if content is ready for current tab
  const isContentReady = metadata?.demo_mode === activeTab && plots && plots.length > 0;

  if (!metadata) {
    return (
      <div className="aq-viewer-empty">
        <p>Loading Aliasing & Quantization visualization...</p>
      </div>
    );
  }

  return (
    <div className="aliasing-quantization-viewer">
      {/* Tab Navigation */}
      <TabBar activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Tab Content */}
      <div className="aq-tab-content">
        {isLoading && !isContentReady ? (
          <LoadingSpinner message={`Loading ${activeTab === 'aliasing' ? 'Audio Aliasing' : activeTab === 'quantization' ? 'Audio Quantization' : 'Image Quantization'}...`} />
        ) : (
          <>
            {activeTab === 'aliasing' && (
              <AliasingTab metadata={metadata} plots={plots} />
            )}

            {activeTab === 'quantization' && (
              <QuantizationTab metadata={metadata} plots={plots} />
            )}

            {activeTab === 'image' && (
              <ImageTab metadata={metadata} plots={plots} />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default memo(AliasingQuantizationViewer);
