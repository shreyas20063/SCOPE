/**
 * SimulationPage
 *
 * Page component for displaying individual simulations.
 * Uses HTTP with debounced updates.
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useSimulation } from '../hooks/useSimulation';
import SimulationViewer from '../components/SimulationViewer';
import SimulationLaunchAnimation from '../components/SimulationLaunchAnimation';
import ErrorMessage from '../components/ErrorMessage';
import { useKeyboardShortcuts } from '../components/KeyboardShortcuts';
import api from '../services/api';
import { decodeParamsForControls } from '../utils/urlParams';

const DEFAULT_TITLE = 'SCOPE';

// Tool-style viewers that hide the standard ControlPanel (and its "Reset to
// Defaults" button) — mirrors the controls-section condition in
// SimulationViewer.jsx. The R shortcut must not reach a reset the user can't see.
const VIEWERS_WITHOUT_CONTROL_PANEL = new Set(['block_diagram_builder', 'signal_flow_scope']);

/**
 * Loose equality between a requested parameter value and what the backend
 * reports back (numbers may come back as floats, select values as strings).
 */
function sameParamValue(requested, actual) {
  if (typeof requested === 'number' && typeof actual === 'number') {
    return Math.abs(requested - actual) <= 1e-9 * Math.max(1, Math.abs(requested), Math.abs(actual));
  }
  return String(requested) === String(actual);
}

/**
 * Error text for a failed API result ({success: false, error, details}).
 */
function describeFailure(result, fallback) {
  return result?.error || result?.details || fallback;
}

function SimulationPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const {
    simulation,
    currentParams,
    plots,
    metadata,
    isLoading,
    isUpdating,
    error,
    isRunning,
    updateParam,
    resetToDefaults,
    handleButtonAction,
    stepForward,
    stepBackward,
    setMetadata,
    hubMismatch,
  } = useSimulation(id);

  const [animationComplete, setAnimationComplete] = useState(false);
  const [pageError, setPageError] = useState(null);

  const handleAnimationComplete = useCallback(() => {
    setAnimationComplete(true);
  }, []);

  // Reset animation (and any share-link error) when simulation changes
  useEffect(() => {
    setAnimationComplete(false);
    setPageError(null);
  }, [id]);

  const simulationReady = !!simulation && simulation.id === id;

  // Name the simulation in the tab title (WCAG 2.4.2)
  useEffect(() => {
    if (simulationReady && simulation.name) {
      document.title = `${simulation.name} | ${DEFAULT_TITLE}`;
    }
  }, [simulationReady, simulation?.name]);

  useEffect(() => () => {
    document.title = DEFAULT_TITLE;
  }, []);

  /**
   * Resync the hook's plots/parameters/metadata from the backend's actual
   * state. execute('update') with no params returns get_state() (main.py),
   * and handleButtonAction applies plots, parameters and metadata from it.
   */
  const resyncFromBackend = useCallback(
    () => handleButtonAction('update', {}),
    [handleButtonAction]
  );

  // ── Share links: apply URL parameters once the initial load has settled ──
  // Runs after the hook's GET /state and hub auto-read (isLoading false), so
  // neither can overwrite the shared values. Keys are validated against the
  // catalog controls, sent in URL order, and any key a later side effect
  // overwrote (e.g. a preset applied after a slider) is sent once more.
  const restoreKey = location.search ? `${id}${location.search}` : null;
  const [settledRestoreKey, setSettledRestoreKey] = useState(null);
  const restoreInFlightRef = useRef(null);
  const urlRestorePending = restoreKey !== null && settledRestoreKey !== restoreKey;

  // Lets an in-flight restore notice the user navigated away (the page stays
  // mounted across /simulation/:id changes) before it touches state or the URL.
  const mountedRef = useRef(true);
  const currentRestoreKeyRef = useRef(restoreKey);
  currentRestoreKeyRef.current = restoreKey;
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (!urlRestorePending || !simulationReady || isLoading) return;
    if (restoreInFlightRef.current === restoreKey) return;

    const urlParams = decodeParamsForControls(location.search, simulation.controls);
    if (!simulation.has_simulator || Object.keys(urlParams).length === 0) {
      setSettledRestoreKey(restoreKey);
      return;
    }

    restoreInFlightRef.current = restoreKey;
    const { pathname, search, hash } = location;
    const stillCurrent = () => mountedRef.current && currentRestoreKeyRef.current === restoreKey;

    (async () => {
      let result = await api.updateParameters(id, urlParams);
      if (result.success && stillCurrent()) {
        const drifted = {};
        Object.entries(urlParams).forEach(([name, value]) => {
          if (name in result.parameters && !sameParamValue(value, result.parameters[name])) {
            drifted[name] = value;
          }
        });
        if (Object.keys(drifted).length > 0) {
          result = await api.updateParameters(id, drifted);
        }
      }

      if (!stillCurrent()) {
        restoreInFlightRef.current = null;
        return;
      }
      await resyncFromBackend();
      restoreInFlightRef.current = null;
      if (!stillCurrent()) return;

      if (result.success) {
        setPageError(null);
        // Drop the consumed keys so a reload keeps the user's later changes
        // instead of re-applying the link. Unrelated query keys are kept.
        const remaining = new URLSearchParams(search);
        const known = new Set([
          ...simulation.controls.map(c => c.name),
          ...Object.keys(result.parameters || {}),
        ]);
        [...remaining.keys()].forEach(key => {
          if (known.has(key)) remaining.delete(key);
        });
        const nextSearch = remaining.toString();
        navigate({ pathname, search: nextSearch ? `?${nextSearch}` : '', hash }, { replace: true });
      } else {
        setPageError(`Couldn't apply the shared link's parameters: ${describeFailure(result, 'request failed')}`);
      }
      setSettledRestoreKey(restoreKey);
    })();
  }, [urlRestorePending, simulationReady, isLoading, restoreKey, location, simulation, id, navigate, resyncFromBackend]);

  // ── Failed updates: surface them and resync controls to the backend ──
  // The hook stores update/reset failures in `error` but the page only
  // rendered it when the catalog itself failed to load, so a rejected change
  // left the controls showing values the plots never received.
  const [errorDismissed, setErrorDismissed] = useState(false);
  const prevUpdatingRef = useRef(isUpdating);
  // Set by user edits/resets so a failure can be told apart from an older
  // error that is still set while some other request (e.g. a step) finishes.
  const userChangePendingRef = useRef(false);

  const handleParamChange = useCallback((name, value) => {
    userChangePendingRef.current = true;
    updateParam(name, value);
  }, [updateParam]);

  const handleReset = useCallback(() => {
    userChangePendingRef.current = true;
    return resetToDefaults();
  }, [resetToDefaults]);

  useEffect(() => {
    setErrorDismissed(false);
  }, [error, pageError]);

  useEffect(() => {
    const finished = prevUpdatingRef.current && !isUpdating;
    prevUpdatingRef.current = isUpdating;
    if (!finished || !userChangePendingRef.current) return;
    userChangePendingRef.current = false;
    if (!error || !simulationReady || !simulation.has_simulator) return;
    // A user change just failed: show the toast again even if an earlier one
    // with the same message was dismissed, and pull the backend's actual
    // values back into the controls.
    setErrorDismissed(false);
    // Don't clobber text the user is still typing (expression fields sync
    // their draft from the controlled value).
    const active = document.activeElement;
    if (active?.tagName === 'TEXTAREA' || (active?.tagName === 'INPUT' && /^(text|search)?$/.test(active.type))) {
      return;
    }
    resyncFromBackend();
  }, [isUpdating, error, simulationReady, simulation?.has_simulator, resyncFromBackend]);

  const bannerError = errorDismissed ? null : (pageError || (simulation ? error : null));

  // ── Page-level keyboard shortcuts (App handles ? and D) ──
  const simType = metadata?.simulation_type ?? simulation?.id;
  const hasControlPanel = simulationReady && (simulation.controls?.length ?? 0) > 0
    && !VIEWERS_WITHOUT_CONTROL_PANEL.has(simType);
  const hasPlayPause = simulationReady
    && !!simulation.controls?.some(c => c.type === 'button' && c.name === 'play_pause');

  const togglePlayPause = useCallback(() => handleButtonAction('play_pause'), [handleButtonAction]);

  useKeyboardShortcuts({
    onReset: hasControlPanel && simulation.has_simulator ? handleReset : undefined,
    onToggleAnimation: hasPlayPause ? togglePlayPause : undefined,
    onEscape: hasPlayPause && isRunning ? togglePlayPause : undefined,
  });

  // Show error state (only if catalog failed to load)
  if (error && !simulation) {
    return (
      <div className="simulation-page">
        <ErrorMessage
          error={error}
          title="Failed to load simulation"
          showBackButton
        />
      </div>
    );
  }

  return (
    <div className={`simulation-page ${animationComplete ? 'page-ready' : ''}`}>
      {/* Launch animation overlay */}
      {!animationComplete && !error && (
        <SimulationLaunchAnimation
          simulationName={simulation?.name || null}
          category={simulation?.category || null}
          categoryColor={simulation?.category_info?.color || null}
          isDataReady={!isLoading && !urlRestorePending}
          onComplete={handleAnimationComplete}
        />
      )}

      {/* Simulation viewer (mounts behind overlay, visible after animation) */}
      {simulation && (
        <SimulationViewer
          simulation={simulation}
          plots={plots}
          metadata={metadata}
          currentParams={currentParams}
          onParamChange={handleParamChange}
          onMetadataChange={setMetadata}
          onReset={handleReset}
          onButtonClick={handleButtonAction}
          onStepForward={stepForward}
          onStepBackward={stepBackward}
          isLoading={isLoading}
          isUpdating={isUpdating}
          isRunning={isRunning}
          hubMismatch={hubMismatch}
        />
      )}

      {/* Non-blocking error toast for failed updates while a simulation is loaded */}
      {simulation && bannerError && (
        <div className="toast-container simulation-error-toast-container">
          <div className="toast toast-error simulation-error-toast" role="alert">
            <span className="toast-icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </span>
            <span className="toast-message">
              {pageError || `Update failed: ${bannerError}`}
            </span>
            <button
              type="button"
              className="toast-close"
              onClick={() => setErrorDismissed(true)}
              aria-label="Dismiss error"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default SimulationPage;
