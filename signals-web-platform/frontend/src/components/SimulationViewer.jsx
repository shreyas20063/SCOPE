/**
 * SimulationViewer Component
 *
 * Main component for displaying and interacting with simulations.
 * Combines PlotDisplay and ControlPanel in a responsive layout.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PlotDisplay from './PlotDisplay';
import ControlPanel from './ControlPanel';
import ShareButton from './ShareButton';
import FurutaPendulum3D from './FurutaPendulum3D';
import FourierPhaseMagnitudeViewer from './FourierPhaseMagnitudeViewer';
import ModulationViewer from './ModulationViewer';
import LensOpticsViewer from './LensOpticsViewer';
import AliasingQuantizationViewer from './AliasingQuantizationViewer';
import ConvolutionViewer from './ConvolutionViewer';
import RCLowpassViewer from './RCLowpassViewer';
import '../styles/SimulationViewer.css';

/**
 * Breadcrumb navigation
 */
function Breadcrumb({ simulation }) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <ol>
        <li>
          <Link to="/">Home</Link>
        </li>
        <li className="separator">/</li>
        <li className="current" aria-current="page">
          {simulation?.name || 'Simulation'}
        </li>
      </ol>
    </nav>
  );
}

/**
 * Mobile tab switcher
 */
function MobileTabSwitcher({ activeTab, onTabChange, hasControls = true }) {
  // Don't render if no controls
  if (!hasControls) return null;

  return (
    <div className="mobile-tabs">
      <button
        className={`tab-button ${activeTab === 'plots' ? 'active' : ''}`}
        onClick={() => onTabChange('plots')}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
        Plots
      </button>
      <button
        className={`tab-button ${activeTab === 'controls' ? 'active' : ''}`}
        onClick={() => onTabChange('controls')}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="4" y1="21" x2="4" y2="14" />
          <line x1="4" y1="10" x2="4" y2="3" />
          <line x1="12" y1="21" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12" y2="3" />
          <line x1="20" y1="21" x2="20" y2="16" />
          <line x1="20" y1="12" x2="20" y2="3" />
          <line x1="1" y1="14" x2="7" y2="14" />
          <line x1="9" y1="8" x2="15" y2="8" />
          <line x1="17" y1="16" x2="23" y2="16" />
        </svg>
        Controls
      </button>
    </div>
  );
}

/**
 * Simulation header with title and metadata
 */
function SimulationHeader({ simulation, currentParams }) {
  return (
    <div className="simulation-header">
      <div className="header-content">
        <Link to="/" className="back-button" aria-label="Go back">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
        </Link>
        <div className="header-text">
          <Breadcrumb simulation={simulation} />
          <h1 className="simulation-title">
            {simulation?.thumbnail && (
              <span className="title-icon">{simulation.thumbnail}</span>
            )}
            {simulation?.name || 'Simulation'}
          </h1>
          {simulation?.description && (
            <p className="simulation-description">{simulation.description}</p>
          )}
        </div>
      </div>
      <div className="header-actions">
        <ShareButton params={currentParams} />
        <div className="header-meta">
          {simulation?.category && (
            <span className="category-badge">{simulation.category}</span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Not implemented placeholder
 */
function NotImplementedPlaceholder({ simulation }) {
  return (
    <div className="not-implemented">
      <div className="placeholder-content">
        <span className="placeholder-icon">{simulation?.thumbnail || '📊'}</span>
        <h3>Simulation Coming Soon</h3>
        <p>
          This simulation is not yet implemented on the web platform.
          Check back later for updates!
        </p>
        <Link to="/" className="btn btn-primary">
          Browse Other Simulations
        </Link>
      </div>
    </div>
  );
}

/**
 * Convolution Info Panel
 * Displays mode, signals, formula, and current value with polished styling
 */
function ConvolutionInfoPanel({ metadata, params }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'convolution_simulator') {
    return null;
  }

  const mode = params?.mode || 'continuous';
  const isContinuous = mode === 'continuous';
  const inputMode = params?.input_mode || 'preset';
  const currentValue = metadata?.current_y_value;
  const timeShift = params?.time_shift ?? 0;
  const hasValue = currentValue !== undefined && currentValue !== null;

  // Get signal expressions
  const signalX = inputMode === 'custom'
    ? (params?.custom_x || 'rect(t)')
    : (metadata?.signal_x_expr || 'rect(t)');
  const signalH = inputMode === 'custom'
    ? (params?.custom_h || 'exp(-t)·u(t)')
    : (metadata?.signal_h_expr || 'exp(-t)·u(t)');

  return (
    <div className="convolution-info-panel">
      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          Convolution
          <span className={`mode-chip ${isContinuous ? 'continuous' : 'discrete'}`}>
            {isContinuous ? 'Continuous' : 'Discrete'}
          </span>
        </h4>

        {/* Signals Row */}
        <div className="info-cards-row">
          {/* Signal x(t) */}
          <div className="info-card signal-x-card">
            <div className="info-card-header">
              <span className="info-card-icon signal-x">{isContinuous ? 'x(t)' : 'x[n]'}</span>
              <span className="info-card-label">Input Signal</span>
            </div>
            <div className="info-card-value signal-expression">{signalX}</div>
          </div>

          {/* Signal h(t) */}
          <div className="info-card signal-h-card">
            <div className="info-card-header">
              <span className="info-card-icon signal-h">{isContinuous ? 'h(t)' : 'h[n]'}</span>
              <span className="info-card-label">Impulse Response</span>
            </div>
            <div className="info-card-value signal-expression">{signalH}</div>
          </div>
        </div>

        {/* Formula Display */}
        <div className="info-card formula-card">
          <div className="info-card-header">
            <span className="info-card-icon result-y">{isContinuous ? 'y(t)' : 'y[n]'}</span>
            <span className="info-card-label">Convolution Result</span>
          </div>
          <div className="convolution-formula-display">
            <div className="formula-line">
              <span className="formula-lhs">{isContinuous ? `y(${timeShift.toFixed(1)})` : `y[${Math.round(timeShift)}]`}</span>
              <span className="formula-equals">=</span>
              <span className="formula-integral">
                {isContinuous ? (
                  <>
                    <span className="integral-symbol">∫</span>
                    <span className="integral-limits">
                      <span className="limit-top">∞</span>
                      <span className="limit-bottom">-∞</span>
                    </span>
                    <span className="integrand">x(τ)h({timeShift.toFixed(1)}-τ)dτ</span>
                  </>
                ) : (
                  <>
                    <span className="sum-symbol">Σ</span>
                    <span className="sum-limits">
                      <span className="limit-top">∞</span>
                      <span className="limit-bottom">k=-∞</span>
                    </span>
                    <span className="summand">x[k]h[{Math.round(timeShift)}-k]</span>
                  </>
                )}
              </span>
              {hasValue && (
                <>
                  <span className="formula-approx">≈</span>
                  <span className="formula-result">{Number(currentValue).toFixed(4)}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Time Position Indicator */}
        <div className="time-position-display">
          <span className="time-chip">
            {isContinuous ? `t₀ = ${timeShift.toFixed(2)} s` : `n₀ = ${Math.round(timeShift)}`}
          </span>
          <span className="source-chip">
            {inputMode === 'preset' ? 'Demo Preset' : 'Custom Expression'}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * DC Motor System Info Panel
 * Displays block diagram, transfer function, poles, and steady-state info
 */
function DCMotorInfoPanel({ metadata }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'dc_motor_feedback_control') {
    return null;
  }

  const { block_diagram_image, system_info, current_params } = metadata;

  return (
    <div className="dc-motor-info-panel">
      {/* Block Diagram */}
      {block_diagram_image && (
        <div className="block-diagram-section">
          <h4 className="info-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            Feedback Control Block Diagram
          </h4>
          <div className="block-diagram-container">
            <img
              src={block_diagram_image}
              alt="Feedback Control Block Diagram"
              className="block-diagram-image"
            />
          </div>
        </div>
      )}

      {/* System Information */}
      {system_info && (
        <div className="system-info-section">
          <h4 className="info-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            System Analysis ({system_info.model_type})
          </h4>

          {/* Transfer Function */}
          <div className="info-card transfer-function-card">
            <div className="info-card-header">
              <span className="info-card-icon">H(s)</span>
              <span className="info-card-label">Transfer Function</span>
            </div>
            <div className="transfer-function-display">
              <div className="tf-symbolic">{system_info.transfer_function.symbolic}</div>
              <div className="tf-equals">=</div>
              <div className="tf-fraction">
                <span className="tf-numerator">{system_info.transfer_function.numerator}</span>
                <span className="tf-line"></span>
                <span className="tf-denominator">{system_info.transfer_function.denominator}</span>
              </div>
            </div>
          </div>

          {/* Poles and Steady State in a row */}
          <div className="info-cards-row">
            {/* Poles */}
            <div className={`info-card poles-card ${system_info.pole_type.includes('Oscillatory') ? 'oscillatory' : 'stable'}`}>
              <div className="info-card-header">
                <span className="info-card-icon">×</span>
                <span className="info-card-label">System Poles</span>
              </div>
              <div className="info-card-value">{system_info.poles}</div>
              <div className="info-card-badge">
                {system_info.pole_type.includes('Oscillatory') ? '🔄 ' : '✓ '}
                {system_info.pole_type}
              </div>
            </div>

            {/* Steady State */}
            <div className="info-card steady-state-card">
              <div className="info-card-header">
                <span className="info-card-icon">∞</span>
                <span className="info-card-label">Steady-State Value</span>
              </div>
              <div className="info-card-value">1/β = {system_info.steady_state_value}</div>
              <div className="info-card-subtext">Final value for unit step input</div>
            </div>
          </div>

          {/* Current Parameters */}
          {current_params && (
            <div className="current-params-display">
              <span className="param-chip alpha">α = {current_params.alpha}</span>
              <span className="param-chip beta">β = {current_params.beta}</span>
              <span className="param-chip gamma">γ = {current_params.gamma}</span>
              {current_params.p !== null && (
                <span className="param-chip p">p = {current_params.p}</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Second-Order System Info Panel
 * Displays system parameters, damping info, poles, and frequency characteristics
 */
function SecondOrderInfoPanel({ metadata }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'second_order_system') {
    return null;
  }

  const { system_info } = metadata;
  if (!system_info) return null;

  // Determine damping style
  const isUnderdamped = system_info.damping_type?.includes('Underdamped');
  const isCritical = system_info.damping_type?.includes('Critically');

  return (
    <div className="second-order-info-panel">
      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Second-Order System Parameters
        </h4>

        {/* Main Parameters Row */}
        <div className="info-cards-row">
          {/* Natural Frequency */}
          <div className="info-card omega-card">
            <div className="info-card-header">
              <span className="info-card-icon">ω₀</span>
              <span className="info-card-label">Natural Frequency</span>
            </div>
            <div className="info-card-value">{system_info.omega_0} rad/s</div>
          </div>

          {/* Quality Factor */}
          <div className="info-card q-card">
            <div className="info-card-header">
              <span className="info-card-icon">Q</span>
              <span className="info-card-label">Quality Factor</span>
            </div>
            <div className="info-card-value">{system_info.Q}</div>
          </div>
        </div>

        {/* Damping Info Row */}
        <div className="info-cards-row">
          {/* Damping Ratio */}
          <div className="info-card zeta-card">
            <div className="info-card-header">
              <span className="info-card-icon">ζ</span>
              <span className="info-card-label">Damping Ratio</span>
            </div>
            <div className="info-card-value">{system_info.zeta}</div>
            <div className={`info-card-badge ${isUnderdamped ? 'underdamped' : isCritical ? 'critical' : 'overdamped'}`}>
              {isUnderdamped ? '🔄 ' : isCritical ? '⚖️ ' : '🎯 '}
              {system_info.damping_type?.split('(')[0]?.trim()}
            </div>
          </div>

          {/* Poles */}
          <div className={`info-card poles-card ${isUnderdamped ? 'oscillatory' : 'stable'}`}>
            <div className="info-card-header">
              <span className="info-card-icon">×</span>
              <span className="info-card-label">System Poles</span>
            </div>
            <div className="info-card-value">{system_info.poles}</div>
            {system_info.pole_magnitude && (
              <div className="info-card-subtext">|p| = {system_info.pole_magnitude}</div>
            )}
          </div>
        </div>

        {/* Frequency Characteristics Row */}
        <div className="info-cards-row">
          {/* Bandwidth */}
          <div className="info-card bandwidth-card">
            <div className="info-card-header">
              <span className="info-card-icon">Δω</span>
              <span className="info-card-label">3dB Bandwidth</span>
            </div>
            <div className="info-card-value">{system_info.bandwidth} rad/s</div>
          </div>

          {/* Resonant Frequency */}
          <div className="info-card resonance-card">
            <div className="info-card-header">
              <span className="info-card-icon">ωᵣ</span>
              <span className="info-card-label">Resonant Frequency</span>
            </div>
            <div className="info-card-value">
              {system_info.resonant_freq ? `${system_info.resonant_freq} rad/s` : 'N/A (Q ≤ 0.707)'}
            </div>
            {!system_info.resonant_freq && (
              <div className="info-card-subtext">No resonance peak</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * CT/DT Poles Info Panel
 * Displays method, poles, and stability information for pole conversion simulation
 */
function CTDTPolesInfoPanel({ metadata }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'ct_dt_poles') {
    return null;
  }

  const { system_info } = metadata;
  if (!system_info) return null;

  // Method display names
  const methodNames = {
    forward_euler: 'Forward Euler',
    backward_euler: 'Backward Euler',
    trapezoidal: 'Trapezoidal (Bilinear)',
  };

  // Format DT pole for display
  const formatDTPole = () => {
    const real = system_info.z_pole_real;
    const imag = system_info.z_pole_imag;
    if (Math.abs(imag) < 0.0001) {
      return `z = ${real}`;
    }
    const sign = imag >= 0 ? '+' : '-';
    return `z = ${real} ${sign} j${Math.abs(imag).toFixed(4)}`;
  };

  // Performance badge style
  const perfBadgeClass = {
    EXCELLENT: 'excellent',
    GOOD: 'good',
    FAIR: 'fair',
    POOR: 'poor',
    UNSTABLE: 'unstable',
  };

  return (
    <div className="ct-dt-poles-info-panel">
      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          CT → DT Pole Conversion
        </h4>

        {/* Method and T/τ Ratio Row */}
        <div className="info-cards-row">
          {/* Transformation Method */}
          <div className="info-card method-card">
            <div className="info-card-header">
              <span className="info-card-icon">f</span>
              <span className="info-card-label">Method</span>
            </div>
            <div className="info-card-value">{methodNames[system_info.method] || system_info.method}</div>
          </div>

          {/* T/τ Ratio */}
          <div className="info-card ratio-card">
            <div className="info-card-header">
              <span className="info-card-icon">T/τ</span>
              <span className="info-card-label">Step Size Ratio</span>
            </div>
            <div className="info-card-value">{system_info.t_tau_ratio}</div>
            <div className="info-card-subtext">T = {system_info.T}s, τ = {system_info.tau}s</div>
          </div>
        </div>

        {/* Poles Row */}
        <div className="info-cards-row">
          {/* CT Pole (s-domain) */}
          <div className="info-card s-pole-card">
            <div className="info-card-header">
              <span className="info-card-icon">s</span>
              <span className="info-card-label">CT Pole (s-domain)</span>
            </div>
            <div className="info-card-value">s = {system_info.s_pole}</div>
            <div className="info-card-subtext">Time constant τ = {system_info.tau}s</div>
          </div>

          {/* DT Pole (z-domain) */}
          <div className={`info-card z-pole-card ${system_info.is_stable ? 'stable' : 'unstable'}`}>
            <div className="info-card-header">
              <span className="info-card-icon">z</span>
              <span className="info-card-label">DT Pole (z-domain)</span>
            </div>
            <div className="info-card-value">{formatDTPole()}</div>
            <div className="info-card-subtext">|z| = {system_info.z_magnitude}</div>
          </div>
        </div>

        {/* Stability and Performance Row */}
        <div className="info-cards-row">
          {/* Stability Status */}
          <div className={`info-card stability-card ${system_info.is_stable ? 'stable' : 'unstable'}`}>
            <div className="info-card-header">
              <span className="info-card-icon">{system_info.is_stable ? '✓' : '!'}</span>
              <span className="info-card-label">Stability</span>
            </div>
            <div className="info-card-value">{system_info.is_stable ? 'STABLE' : 'UNSTABLE'}</div>
            <div className={`info-card-badge ${system_info.is_stable ? 'stable' : 'unstable'}`}>
              {system_info.is_stable ? '|z| < 1' : '|z| ≥ 1'}
            </div>
          </div>

          {/* Performance Rating */}
          <div className={`info-card performance-card ${perfBadgeClass[system_info.performance_rating] || ''}`}>
            <div className="info-card-header">
              <span className="info-card-icon">★</span>
              <span className="info-card-label">Approximation Quality</span>
            </div>
            <div className="info-card-value">{system_info.performance_rating}</div>
            {system_info.rms_error !== null && (
              <div className="info-card-subtext">RMS Error: {system_info.rms_error}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Furuta Pendulum Info Panel
 * Displays pendulum state, PID gains, and stability status matching PyQt5
 */
function FurutaPendulumInfoPanel({ metadata, animationFrame = { current: 0, total: 0 } }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'furuta_pendulum') {
    return null;
  }

  const { system_info, visualization_3d } = metadata;
  if (!system_info) return null;

  const isStable = system_info.is_stable;
  const settlingTime = system_info.settling_time;

  // Use time-series data if available, otherwise fall back to static final values
  const thetaSeries = visualization_3d?.theta_series || [];
  const phiSeries = visualization_3d?.phi_series || [];
  const angularVelSeries = visualization_3d?.angular_velocities || [];
  const torqueSeries = visualization_3d?.torques || [];

  // Get dynamic values based on current animation frame
  const frameIndex = Math.max(0, Math.min(animationFrame.current, thetaSeries.length > 0 ? thetaSeries.length - 1 : 0));

  // Dynamic values (update with animation) - with safety checks for undefined
  const dynamicTheta = thetaSeries[frameIndex] ?? system_info.theta_deg;
  const dynamicPhi = phiSeries[frameIndex] ?? system_info.phi_deg;
  const dynamicAngularVel = angularVelSeries[frameIndex] ?? [0, 0];
  const dynamicTorque = torqueSeries[frameIndex] ?? system_info.torque;

  // Computed dynamic values
  const theta_deg = typeof dynamicTheta === 'number' ? dynamicTheta.toFixed(1) : system_info.theta_deg;
  const phi_deg = typeof dynamicPhi === 'number' ? dynamicPhi.toFixed(1) : system_info.phi_deg;
  const theta_dot_deg = Array.isArray(dynamicAngularVel) ? (dynamicAngularVel[0] * 180 / Math.PI).toFixed(1) : system_info.theta_dot_deg;
  const phi_dot_deg = Array.isArray(dynamicAngularVel) ? (dynamicAngularVel[1] * 180 / Math.PI).toFixed(1) : system_info.phi_dot_deg;
  const torque = typeof dynamicTorque === 'number' ? dynamicTorque.toFixed(3) : system_info.torque;
  const height = visualization_3d?.pendulum_length ? (visualization_3d.pendulum_length * Math.cos(dynamicTheta * Math.PI / 180)).toFixed(3) : system_info.height;

  // Direction based on dynamic values
  const armDirection = parseFloat(phi_dot_deg) > 5 ? 'CCW' : (parseFloat(phi_dot_deg) < -5 ? 'CW' : 'STOPPED');
  const torqueDirection = parseFloat(torque) > 0.01 ? 'CCW' : (parseFloat(torque) < -0.01 ? 'CW' : 'ZERO');

  return (
    <div className="furuta-pendulum-info-panel">
      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="12" x2="15" y2="15"/>
          </svg>
          Furuta Pendulum Control
          <span className={`status-chip ${isStable ? 'stable' : 'unstable'}`}>
            {isStable ? '✓ Stable' : '⚠ Unstable'}
          </span>
        </h4>

        {/* Physical Parameters Row */}
        <div className="info-cards-row">
          {/* Pendulum State */}
          <div className="info-card pendulum-state-card">
            <div className="info-card-header">
              <span className="info-card-icon">θ</span>
              <span className="info-card-label">Pendulum Angle</span>
            </div>
            <div className="info-card-value">{theta_deg}°</div>
            <div className="info-card-subtext">
              ω = {theta_dot_deg}°/s
            </div>
          </div>

          {/* Arm State */}
          <div className="info-card arm-state-card">
            <div className="info-card-header">
              <span className="info-card-icon">φ</span>
              <span className="info-card-label">Arm Rotation</span>
            </div>
            <div className="info-card-value">{phi_deg}°</div>
            <div className="info-card-subtext">
              Direction: {armDirection}
            </div>
          </div>
        </div>

        {/* Control & Height Row */}
        <div className="info-cards-row">
          {/* Control Torque */}
          <div className={`info-card torque-card ${torqueDirection === 'ZERO' ? 'zero' : ''}`}>
            <div className="info-card-header">
              <span className="info-card-icon">τ</span>
              <span className="info-card-label">Control Torque</span>
            </div>
            <div className="info-card-value">{torque} Nm</div>
            <div className="info-card-subtext">
              {torqueDirection}
            </div>
          </div>

          {/* Pendulum Height */}
          <div className="info-card height-card">
            <div className="info-card-header">
              <span className="info-card-icon">h</span>
              <span className="info-card-label">Pendulum Height</span>
            </div>
            <div className="info-card-value">{height} m</div>
            <div className="info-card-subtext">
              Max: {system_info.pendulum_length} m
            </div>
          </div>
        </div>

        {/* PID Gains Display */}
        <div className="pid-gains-display">
          <span className="pid-chip kp">Kp = {system_info.Kp}</span>
          <span className="pid-chip kd">Kd = {system_info.Kd}</span>
          <span className="pid-chip ki">Ki = {system_info.Ki}</span>
        </div>

        {/* Physical Properties */}
        <div className="physical-props-display">
          <span className="prop-chip mass">m = {system_info.mass} kg</span>
          <span className="prop-chip length">L = {system_info.pendulum_length} m</span>
          <span className="prop-chip arm">r = {system_info.arm_length} m</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Fourier Phase vs Magnitude Info Panel
 * Displays analysis mode, quality metrics, and key insight about phase importance
 */
function FourierPhaseMagnitudeInfoPanel({ metadata }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'fourier_phase_vs_magnitude') {
    return null;
  }

  const { system_info } = metadata;
  if (!system_info) return null;

  const isImageMode = system_info.mode?.toLowerCase().includes('image');

  // Format pattern/signal names for display
  const formatName = (name) => {
    if (!name) return 'N/A';
    return name.charAt(0).toUpperCase() + name.slice(1);
  };

  // Format mode names (handles both raw and pre-formatted values)
  const formatMode = (mode) => {
    if (!mode) return 'Original';
    const m = mode.toLowerCase().replace(/\s+/g, '_');
    if (m === 'uniform_magnitude') return 'Uniform Mag';
    if (m === 'uniform_phase') return 'Uniform Phase';
    if (m === 'original') return 'Original';
    return mode; // Return as-is if already formatted
  };

  return (
    <div className="fourier-phase-mag-info-panel">
      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
          </svg>
          Fourier Analysis: Phase vs Magnitude
          <span className={`mode-chip ${isImageMode ? 'image' : 'audio'}`}>
            {isImageMode ? '🖼️ Image' : '🔊 Audio'}
          </span>
        </h4>

        {/* Source Selection Row */}
        <div className="info-cards-row">
          {/* Source 1 Card */}
          <div className="info-card source1-card">
            <div className="info-card-header">
              <span className="info-card-icon source1">1</span>
              <span className="info-card-label">
                {isImageMode ? 'Image 1' : 'Signal 1'}
              </span>
            </div>
            <div className="info-card-value">
              {isImageMode
                ? formatName(system_info.image1_pattern)
                : formatName(system_info.audio1_type)
              }
            </div>
            <div className="info-card-subtext">
              Mode: {isImageMode
                ? formatMode(system_info.image1_mode)
                : 'Original'
              }
            </div>
          </div>

          {/* Source 2 Card */}
          <div className="info-card source2-card">
            <div className="info-card-header">
              <span className="info-card-icon source2">2</span>
              <span className="info-card-label">
                {isImageMode ? 'Image 2' : 'Signal 2'}
              </span>
            </div>
            <div className="info-card-value">
              {isImageMode
                ? formatName(system_info.image2_pattern)
                : formatName(system_info.audio2_type)
              }
            </div>
            <div className="info-card-subtext">
              Mode: {isImageMode
                ? formatMode(system_info.image2_mode)
                : 'Original'
              }
            </div>
          </div>
        </div>

        {/* Quality Metrics Row */}
        <div className="info-cards-row">
          {/* Source 1 Metrics */}
          <div className="info-card metrics1-card">
            <div className="info-card-header">
              <span className="info-card-icon metrics">📊</span>
              <span className="info-card-label">{isImageMode ? 'Image 1' : 'Audio 1'} Quality</span>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">MSE:</span>
                <span className="metric-value mse">
                  {isImageMode ? system_info.image1_mse : system_info.audio1_mse}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Corr:</span>
                <span className="metric-value corr">
                  {isImageMode ? system_info.image1_correlation : system_info.audio1_correlation}
                </span>
              </div>
              {isImageMode && (
                <div className="metric-item">
                  <span className="metric-label">SSIM:</span>
                  <span className="metric-value ssim">{system_info.image1_ssim}</span>
                </div>
              )}
              {!isImageMode && (
                <div className="metric-item">
                  <span className="metric-label">SNR:</span>
                  <span className="metric-value snr">{system_info.audio1_snr}</span>
                </div>
              )}
            </div>
          </div>

          {/* Source 2 Metrics */}
          <div className="info-card metrics2-card">
            <div className="info-card-header">
              <span className="info-card-icon metrics">📊</span>
              <span className="info-card-label">{isImageMode ? 'Image 2' : 'Audio 2'} Quality</span>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">MSE:</span>
                <span className="metric-value mse">
                  {isImageMode ? system_info.image2_mse : system_info.audio2_mse}
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Corr:</span>
                <span className="metric-value corr">
                  {isImageMode ? system_info.image2_correlation : system_info.audio2_correlation}
                </span>
              </div>
              {isImageMode && (
                <div className="metric-item">
                  <span className="metric-label">SSIM:</span>
                  <span className="metric-value ssim">{system_info.image2_ssim}</span>
                </div>
              )}
              {!isImageMode && (
                <div className="metric-item">
                  <span className="metric-label">SNR:</span>
                  <span className="metric-value snr">{system_info.audio2_snr}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Hybrid Comparison Metrics */}
        {(system_info.hybrid1_correlation || system_info.hybrid2_correlation) && (
          <div className="info-card hybrid-metrics-card">
            <div className="info-card-header">
              <span className="info-card-icon hybrid">⚡</span>
              <span className="info-card-label">Hybrid Phase Dominance</span>
            </div>
            <div className="hybrid-metrics-row">
              <div className="hybrid-metric">
                <div className="hybrid-label">Mag₁ + Phase₂</div>
                <div className="hybrid-values">
                  <span className="hybrid-corr2">
                    → Resembles Src2: {system_info.hybrid1_correlation}
                  </span>
                </div>
              </div>
              <div className="hybrid-metric">
                <div className="hybrid-label">Mag₂ + Phase₁</div>
                <div className="hybrid-values">
                  <span className="hybrid-corr1">
                    → Resembles Src1: {system_info.hybrid2_correlation}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Key Insight Message */}
        {system_info.insight && (
          <div className="insight-banner">
            <span className="insight-icon">💡</span>
            <span className="insight-text">{system_info.insight}</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Feedback System Analysis Info Panel
 * Displays open-loop vs closed-loop metrics matching PyQt5 metrics panel
 */
function FeedbackSystemInfoPanel({ metadata }) {
  if (!metadata?.simulation_type || metadata.simulation_type !== 'feedback_system_analysis') {
    return null;
  }

  const { system_info, block_diagram_image } = metadata;
  if (!system_info) return null;

  return (
    <div className="feedback-system-info-panel">
      {/* Block Diagram */}
      {block_diagram_image && (
        <div className="block-diagram-section">
          <h4 className="info-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            Feedback Amplifier Block Diagram
          </h4>
          <div className="block-diagram-container feedback-block-diagram">
            <img
              src={block_diagram_image}
              alt="Feedback Amplifier Block Diagram"
              className="block-diagram-image"
            />
          </div>
        </div>
      )}

      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
          </svg>
          Feedback System Analysis
        </h4>

        {/* Transfer Functions */}
        <div className="info-card tf-card">
          <div className="info-card-header">
            <span className="info-card-icon">H(s)</span>
            <span className="info-card-label">Transfer Functions</span>
          </div>
          <div className="tf-equations">
            <div className="tf-row">
              <span className="tf-label">Open-Loop:</span>
              <span className="tf-formula">{system_info.transfer_function?.open_loop}</span>
            </div>
            <div className="tf-row">
              <span className="tf-label">Closed-Loop:</span>
              <span className="tf-formula">{system_info.transfer_function?.closed_loop}</span>
            </div>
          </div>
        </div>

        {/* Parameters Row */}
        <div className="current-params-display">
          <span className="param-chip beta">β = {system_info.beta}</span>
          <span className="param-chip k0">K₀ = {system_info.K0?.toLocaleString()}</span>
          <span className="param-chip alpha">α = {system_info.alpha} rad/s</span>
          <span className="param-chip input">Input = {system_info.input_amp}V</span>
        </div>

        {/* Open-Loop vs Closed-Loop Metrics */}
        <div className="info-cards-row">
          {/* Open-Loop Metrics */}
          <div className="info-card ol-metrics-card">
            <div className="info-card-header">
              <span className="info-card-icon open-loop">OL</span>
              <span className="info-card-label">Open-Loop</span>
            </div>
            <div className="metrics-list">
              <div className="metric-row">
                <span className="metric-label">Gain:</span>
                <span className="metric-value">{system_info.ol_gain}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Bandwidth:</span>
                <span className="metric-value">{system_info.ol_bw}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Rise Time:</span>
                <span className="metric-value">{system_info.ol_rise_time}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Pole:</span>
                <span className="metric-value">s = {system_info.ol_pole}</span>
              </div>
            </div>
          </div>

          {/* Closed-Loop Metrics */}
          <div className="info-card cl-metrics-card">
            <div className="info-card-header">
              <span className="info-card-icon closed-loop">CL</span>
              <span className="info-card-label">Closed-Loop</span>
            </div>
            <div className="metrics-list">
              <div className="metric-row">
                <span className="metric-label">Gain:</span>
                <span className="metric-value">{system_info.cl_gain}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Bandwidth:</span>
                <span className="metric-value">{system_info.cl_bw}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Rise Time:</span>
                <span className="metric-value">{system_info.cl_rise_time}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Pole:</span>
                <span className="metric-value">s = {system_info.cl_pole}</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

/**
 * Amplifier Topologies Info Panel
 * Displays circuit diagram, mode info, gain parameters, and audio playback matching PyQt5
 */
function AmplifierInfoPanel({ metadata }) {
  const [playingType, setPlayingType] = useState(null); // null, 'input', or 'output'
  const audioContextRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const inputBufferRef = useRef(null);
  const outputBufferRef = useRef(null);

  // Stop audio - defined before useEffect hooks that depend on it
  const stopAudio = useCallback(() => {
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop();
      } catch (e) {}
      sourceNodeRef.current = null;
    }
    setPlayingType(null);
  }, []);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      stopAudio();
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [stopAudio]);

  // Stop playback when metadata changes (parameters updated)
  useEffect(() => {
    stopAudio();
    // Clear buffer cache to force reload with new audio
    inputBufferRef.current = null;
    outputBufferRef.current = null;
  }, [metadata?.audio_output?.data, metadata?.audio_input?.data, stopAudio]);

  if (!metadata?.simulation_type || metadata.simulation_type !== 'amplifier_topologies') {
    return null;
  }

  const { circuit_image, system_info, audio_input, audio_output } = metadata;
  if (!system_info) return null;

  // Mode badge color based on mode type
  const getModeColor = (mode) => {
    switch (mode) {
      case 'Simple Amplifier': return 'simple';
      case 'Feedback System': return 'feedback';
      case 'Crossover Distortion': return 'crossover';
      case 'Compensated System': return 'compensated';
      default: return 'simple';
    }
  };

  // Initialize audio context
  const getAudioContext = async () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    const ctx = audioContextRef.current;
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }
    return ctx;
  };

  // Create audio buffer from data
  const createAudioBuffer = async (audioData, sampleRate) => {
    const ctx = await getAudioContext();
    const buffer = ctx.createBuffer(1, audioData.length, sampleRate);
    const channelData = buffer.getChannelData(0);
    for (let i = 0; i < audioData.length; i++) {
      channelData[i] = audioData[i];
    }
    return buffer;
  };

  // Play Input audio
  const handlePlayInput = async () => {
    if (!audio_input?.data || audio_input.data.length === 0) return;

    try {
      stopAudio();
      const ctx = await getAudioContext();

      if (!inputBufferRef.current) {
        inputBufferRef.current = await createAudioBuffer(audio_input.data, audio_input.sample_rate);
      }

      const source = ctx.createBufferSource();
      source.buffer = inputBufferRef.current;
      source.loop = true;
      source.connect(ctx.destination);
      source.start();
      sourceNodeRef.current = source;
      setPlayingType('input');
    } catch (error) {
      console.error('Error playing input audio:', error);
    }
  };

  // Play Output audio
  const handlePlayOutput = async () => {
    if (!audio_output?.data || audio_output.data.length === 0) return;

    try {
      stopAudio();
      const ctx = await getAudioContext();

      if (!outputBufferRef.current) {
        outputBufferRef.current = await createAudioBuffer(audio_output.data, audio_output.sample_rate);
      }

      const source = ctx.createBufferSource();
      source.buffer = outputBufferRef.current;
      source.loop = true;
      source.connect(ctx.destination);
      source.start();
      sourceNodeRef.current = source;
      setPlayingType('output');
    } catch (error) {
      console.error('Error playing output audio:', error);
    }
  };

  return (
    <div className="amplifier-info-panel">
      {/* Circuit Diagram */}
      {circuit_image && (
        <div className="block-diagram-section">
          <h4 className="info-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            Circuit Diagram
            <span className={`mode-chip ${getModeColor(system_info.mode)}`}>
              {system_info.mode}
            </span>
          </h4>
          <div className="block-diagram-container amplifier-circuit-diagram">
            <img
              src={circuit_image}
              alt={`${system_info.mode} Circuit Diagram`}
              className="block-diagram-image"
            />
          </div>
        </div>
      )}

      {/* Audio Playback Controls - Compact PyQt5-style */}
      {(audio_input || audio_output) && (
        <div className="audio-playback-section compact">
          <div className="audio-source-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
            </svg>
            <span>Input: {system_info.input_source}</span>
          </div>
          <div className="audio-buttons-row">
            <button
              className={`audio-btn-compact input-btn ${playingType === 'input' ? 'playing' : ''}`}
              onClick={playingType === 'input' ? stopAudio : handlePlayInput}
              disabled={!audio_input}
            >
              {playingType === 'input' ? '■' : '▶'} Input
            </button>
            <button
              className={`audio-btn-compact output-btn ${playingType === 'output' ? 'playing' : ''}`}
              onClick={playingType === 'output' ? stopAudio : handlePlayOutput}
              disabled={!audio_output}
            >
              {playingType === 'output' ? '■' : '▶'} Output
            </button>
            {playingType && (
              <button className="audio-btn-compact stop-btn" onClick={stopAudio}>
                ■ Stop
              </button>
            )}
          </div>
          {playingType && (
            <div className="audio-playing-indicator">
              <span className="pulse-dot"></span>
              Playing {playingType === 'input' ? 'Input' : 'Output'} Signal...
            </div>
          )}
        </div>
      )}

      {/* System Information */}
      <div className="system-info-section">
        <h4 className="info-section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Amplifier Analysis
        </h4>

        {/* Mode Description */}
        <div className="info-card mode-description-card">
          <div className="info-card-header">
            <span className="info-card-icon">📋</span>
            <span className="info-card-label">Configuration</span>
          </div>
          <div className="info-card-value">{system_info.mode}</div>
          <div className="info-card-subtext">{system_info.mode_description}</div>
        </div>

        {/* Gain Info Row */}
        <div className="info-cards-row">
          {/* Effective Gain */}
          <div className="info-card gain-card">
            <div className="info-card-header">
              <span className="info-card-icon gain">G</span>
              <span className="info-card-label">Effective Gain</span>
            </div>
            <div className="info-card-value">{system_info.effective_gain}</div>
            <div className="info-card-subtext gain-formula">{system_info.gain_formula}</div>
          </div>

          {/* Ideal Gain */}
          <div className="info-card ideal-gain-card">
            <div className="info-card-header">
              <span className="info-card-icon ideal">1/β</span>
              <span className="info-card-label">Ideal Gain</span>
            </div>
            <div className="info-card-value">{system_info.ideal_gain}</div>
            <div className="info-card-subtext">Feedback target gain</div>
          </div>
        </div>

        {/* Parameters Display */}
        <div className="info-cards-row">
          {/* Forward Gain K */}
          <div className="info-card k-param-card">
            <div className="info-card-header">
              <span className="info-card-icon param-k">K</span>
              <span className="info-card-label">Forward Gain</span>
            </div>
            <div className="info-card-value">{system_info.K}</div>
          </div>

          {/* Power Amp Gain F0 */}
          <div className="info-card f0-param-card">
            <div className="info-card-header">
              <span className="info-card-icon param-f0">F₀</span>
              <span className="info-card-label">Power Amp Gain</span>
            </div>
            <div className="info-card-value">{system_info.F0}</div>
          </div>
        </div>

        {/* Beta and VT Row */}
        <div className="info-cards-row">
          {/* Feedback Factor β */}
          <div className="info-card beta-param-card">
            <div className="info-card-header">
              <span className="info-card-icon param-beta">β</span>
              <span className="info-card-label">Feedback Factor</span>
            </div>
            <div className="info-card-value">{system_info.beta}</div>
          </div>

          {/* Threshold Voltage VT */}
          <div className="info-card vt-param-card">
            <div className="info-card-header">
              <span className="info-card-icon param-vt">Vₜ</span>
              <span className="info-card-label">Threshold Voltage</span>
            </div>
            <div className="info-card-value">{system_info.VT} V</div>
            <div className="info-card-subtext">Crossover dead zone</div>
          </div>
        </div>

        {/* Input Source */}
        <div className="current-params-display">
          <span className="param-chip input-source">
            Input: {system_info.input_source}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Main SimulationViewer component
 */
function SimulationViewer({
  simulation,
  plots = [],
  metadata = null,
  currentParams = {},
  onParamChange,
  onReset,
  onButtonClick,
  onStepForward,
  onStepBackward,
  isLoading = false,
  isUpdating = false,
  isRunning = false,
}) {
  const [mobileActiveTab, setMobileActiveTab] = useState('plots');
  const [animationFrame, setAnimationFrame] = useState({ current: 0, total: 0 });

  // Check if simulation has an active simulator
  const hasSimulator = simulation?.has_simulator;
  const parameters = simulation?.controls || [];

  // Check if controls should be sticky (from metadata)
  const stickyControls = metadata?.sticky_controls === true;

  // Callback for 3D animation frame changes (memoized to prevent re-renders)
  const handleFrameChange = useCallback((currentFrame, totalFrames) => {
    setAnimationFrame({ current: currentFrame, total: totalFrames });
  }, []);

  return (
    <div className={`simulation-viewer ${stickyControls ? 'sticky-controls-mode' : ''}`}>
      <SimulationHeader simulation={simulation} currentParams={currentParams} />

      {!hasSimulator ? (
        <NotImplementedPlaceholder simulation={simulation} />
      ) : (
        <>
          {/* Mobile tab switcher - only visible on small screens when there are controls */}
          <MobileTabSwitcher
            activeTab={mobileActiveTab}
            onTabChange={setMobileActiveTab}
            hasControls={parameters && parameters.length > 0}
          />

          <div className={`viewer-content ${(!parameters || parameters.length === 0) ? 'no-controls' : ''}`}>
            {/* Plots section */}
            <div
              className={`plots-section ${
                mobileActiveTab === 'plots' ? 'mobile-visible' : 'mobile-hidden'
              }`}
            >
              {/* Convolution Info Panel */}
              <ConvolutionInfoPanel metadata={metadata} params={currentParams} />

              {/* DC Motor Info Panel (block diagram & system info) */}
              <DCMotorInfoPanel metadata={metadata} />

              {/* Second-Order System Info Panel */}
              <SecondOrderInfoPanel metadata={metadata} />

              {/* CT/DT Poles Info Panel */}
              <CTDTPolesInfoPanel metadata={metadata} />

              {/* Feedback System Info Panel */}
              <FeedbackSystemInfoPanel metadata={metadata} />

              {/* Amplifier Topologies Info Panel */}
              <AmplifierInfoPanel metadata={metadata} />

              {/* Fourier Phase vs Magnitude Info Panel */}
              <FourierPhaseMagnitudeInfoPanel metadata={metadata} />

              {/* Furuta Pendulum Info Panel */}
              <FurutaPendulumInfoPanel metadata={metadata} animationFrame={animationFrame} />

              {/* Furuta Pendulum 3D Visualization */}
              {metadata?.has_3d_visualization && metadata?.simulation_type === 'furuta_pendulum' && (
                <div className="furuta-3d-section">
                  <h4 className="visualization-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                      <path d="M2 17l10 5 10-5"/>
                      <path d="M2 12l10 5 10-5"/>
                    </svg>
                    3D Visualization
                  </h4>
                  <FurutaPendulum3D
                    visualization3D={metadata?.visualization_3d}
                    isStable={metadata?.system_info?.is_stable || false}
                    onFrameChange={handleFrameChange}
                  />
                </div>
              )}

              {/* Custom viewers for specific simulations */}
              {metadata?.simulation_type === 'fourier_phase_vs_magnitude' && metadata?.has_custom_viewer ? (
                <FourierPhaseMagnitudeViewer
                  metadata={metadata}
                  plots={plots}
                />
              ) : metadata?.simulation_type === 'modulation_techniques' ? (
                <ModulationViewer
                  metadata={metadata}
                  plots={plots}
                  currentParams={currentParams}
                  onParamChange={onParamChange}
                />
              ) : metadata?.simulation_type === 'lens_optics' ? (
                <LensOpticsViewer
                  metadata={metadata}
                  plots={plots}
                />
              ) : metadata?.simulation_type === 'aliasing_quantization' ? (
                <AliasingQuantizationViewer
                  metadata={metadata}
                  plots={plots}
                  currentParams={currentParams}
                  onParamChange={onParamChange}
                />
              ) : metadata?.simulation_type === 'convolution_simulator' ? (
                <ConvolutionViewer
                  metadata={metadata}
                  plots={plots}
                  currentParams={currentParams}
                  onParamChange={onParamChange}
                />
              ) : metadata?.simulation_type === 'rc_lowpass_filter' ? (
                <RCLowpassViewer
                  metadata={metadata}
                  plots={plots}
                />
              ) : (
                <PlotDisplay
                  plots={plots}
                  isLoading={isLoading}
                  emptyMessage={
                    isLoading
                      ? 'Loading plots...'
                      : 'Adjust parameters to generate plots.'
                  }
                />
              )}
            </div>

            {/* Controls section - only show if there are parameters */}
            {parameters && parameters.length > 0 && (
              <div
                className={`controls-section ${
                  mobileActiveTab === 'controls' ? 'mobile-visible' : 'mobile-hidden'
                }`}
              >
                <ControlPanel
                  parameters={parameters}
                  currentValues={currentParams}
                  metadata={metadata}
                  onParamChange={onParamChange}
                  onReset={onReset}
                  onButtonClick={onButtonClick}
                  onStepForward={onStepForward}
                  onStepBackward={onStepBackward}
                  isLoading={isLoading}
                  isUpdating={isUpdating}
                  isRunning={isRunning}
                />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default SimulationViewer;
