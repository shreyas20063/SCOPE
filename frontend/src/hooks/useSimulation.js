/**
 * useSimulation Hook
 *
 * Custom React hook for managing simulation state and API communication.
 * Provides:
 * - Simulation definition loading
 * - Parameter state management
 * - Debounced parameter updates
 * - Plot data management
 * - Loading and error states
 * - Animation support (Play/Pause/Reset)
 *
 * Fixed: Race conditions, overlapping requests, animation state sync
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

const ANIMATION_BASE_INTERVAL = 50; // Base 50ms between frames (like PyQt5)
const DEBOUNCE_WAIT = 150; // Reduced from 500ms for more responsive feel

/**
 * Debounce utility function with cancel support
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function with cancel method
 */
function debounce(func, wait) {
  let timeout;
  const debouncedFn = function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
  debouncedFn.cancel = () => clearTimeout(timeout);
  return debouncedFn;
}

/**
 * Custom hook for managing simulation state
 * @param {string} simId - Simulation ID
 * @returns {Object} Simulation state and methods
 */
export function useSimulation(simId) {
  // State
  const [simulation, setSimulation] = useState(null);
  const [currentParams, setCurrentParams] = useState({});
  const [plots, setPlots] = useState([]);
  const [metadata, setMetadata] = useState(null); // For formula, presets, errors
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);  // Animation state

  // Refs for debouncing, animation, and request locking
  const pendingUpdates = useRef({});
  const debouncedUpdateRef = useRef(null);
  const animationIntervalRef = useRef(null);
  const isAnimatingRef = useRef(false); // Prevent overlapping animation frames
  const isFlushingRef = useRef(false); // Prevent overlapping parameter updates
  const mountedRef = useRef(true); // Track if component is mounted

  /**
   * Validate a parameter value against its definition
   */
  const validateParam = useCallback((paramDef, value) => {
    if (!paramDef) return { valid: true, value };

    let validatedValue = value;

    // Type-specific validation
    switch (paramDef.type) {
      case 'slider':
      case 'number_input':
        validatedValue = Number(value);
        if (isNaN(validatedValue)) {
          return { valid: false, error: 'Must be a number' };
        }
        if (paramDef.min !== undefined && validatedValue < paramDef.min) {
          validatedValue = paramDef.min;
        }
        if (paramDef.max !== undefined && validatedValue > paramDef.max) {
          validatedValue = paramDef.max;
        }
        break;

      case 'checkbox':
        validatedValue = Boolean(value);
        break;

      case 'select':
        const validOptions = paramDef.options?.map(opt =>
          typeof opt === 'object' ? opt.value : opt
        ) || [];
        if (validOptions.length > 0 && !validOptions.includes(value)) {
          return { valid: false, error: 'Invalid option' };
        }
        break;

      default:
        break;
    }

    return { valid: true, value: validatedValue };
  }, []);

  /**
   * Get parameter definition by name
   */
  const getParamDef = useCallback((paramName) => {
    if (!simulation?.controls) return null;
    return simulation.controls.find(p => p.name === paramName);
  }, [simulation]);

  /**
   * Send pending updates to backend
   * Protected against overlapping calls
   */
  const flushUpdates = useCallback(async () => {
    // Skip if already flushing or animation is running (animation handles updates)
    if (isFlushingRef.current) return;

    const updates = { ...pendingUpdates.current };
    pendingUpdates.current = {};

    if (Object.keys(updates).length === 0) return;

    isFlushingRef.current = true;
    setIsUpdating(true);

    try {
      const result = await api.updateParameters(simId, updates);

      if (!mountedRef.current) return;

      if (result.success) {
        setPlots(result.plots || []);
        // Update metadata if present
        if (result.metadata) {
          console.log('[useSimulation flushUpdates] Updating metadata, is_stable:', result.metadata?.system_info?.is_stable);
          setMetadata(result.metadata);
        }
        // Sync animation-related params (like time_shift) from backend
        // but preserve user-controlled params to avoid slider jumping
        if (result.parameters) {
          setCurrentParams(prev => {
            const updated = { ...prev };
            // Only sync params that user isn't actively controlling
            const activeParams = Object.keys(pendingUpdates.current);
            Object.entries(result.parameters).forEach(([key, value]) => {
              if (!activeParams.includes(key)) {
                updated[key] = value;
              }
            });
            return updated;
          });
        }
        setError(null);
      } else {
        setError(result.error || 'Failed to update parameters');
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message || 'Update failed');
      }
    } finally {
      isFlushingRef.current = false;
      if (mountedRef.current) {
        setIsUpdating(false);
      }
    }
  }, [simId]);

  // Create debounced update function
  useEffect(() => {
    debouncedUpdateRef.current = debounce(flushUpdates, DEBOUNCE_WAIT);
    return () => {
      if (debouncedUpdateRef.current?.cancel) {
        debouncedUpdateRef.current.cancel();
      }
    };
  }, [flushUpdates]);

  /**
   * Update a single parameter
   * Updates are batched and debounced
   */
  const updateParam = useCallback((paramName, value) => {
    // Validate the parameter
    const paramDef = getParamDef(paramName);
    const validation = validateParam(paramDef, value);

    if (!validation.valid) {
      console.warn(`Invalid value for ${paramName}: ${validation.error}`);
      return;
    }

    // Update local state immediately for responsive UI
    setCurrentParams(prev => ({
      ...prev,
      [paramName]: validation.value,
    }));

    // Queue the update
    pendingUpdates.current[paramName] = validation.value;

    // Trigger debounced backend update
    if (debouncedUpdateRef.current) {
      debouncedUpdateRef.current();
    }
  }, [getParamDef, validateParam]);

  /**
   * Update multiple parameters at once
   */
  const updateParams = useCallback((params) => {
    Object.entries(params).forEach(([name, value]) => {
      updateParam(name, value);
    });
  }, [updateParam]);

  /**
   * Set parameters from URL (bypasses debounce for immediate update)
   */
  const setParamsFromUrl = useCallback(async (urlParams) => {
    if (Object.keys(urlParams).length === 0) return;

    // Validate and merge with current params
    const validatedParams = {};
    Object.entries(urlParams).forEach(([name, value]) => {
      const paramDef = simulation?.controls?.find(p => p.name === name || p.id === name);
      const validation = validateParam(paramDef, value);
      if (validation.valid) {
        validatedParams[name] = validation.value;
      }
    });

    if (Object.keys(validatedParams).length === 0) return;

    // Update local state immediately
    setCurrentParams(prev => ({
      ...prev,
      ...validatedParams,
    }));

    // Send to backend immediately (no debounce for URL params)
    setIsUpdating(true);
    try {
      const result = await api.updateParameters(simId, validatedParams);
      if (result.success) {
        setPlots(result.plots || []);
        setError(null);
      }
    } catch (err) {
      console.warn('Failed to apply URL parameters:', err);
    } finally {
      setIsUpdating(false);
    }
  }, [simId, simulation?.controls, validateParam]);

  /**
   * Initialize simulation with parameters
   */
  const initializeSimulation = useCallback(async (initialParams = {}) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await api.initializeSimulation(simId, initialParams);

      if (result.success) {
        setPlots(result.plots || []);
        if (result.parameters) {
          setCurrentParams(result.parameters);
        }
        return { success: true };
      } else {
        setError(result.error || 'Initialization failed');
        return { success: false, error: result.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Initialization failed';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setIsLoading(false);
    }
  }, [simId]);

  /**
   * Reset simulation to default parameters
   */
  const resetToDefaults = useCallback(async () => {
    // Stop animation when resetting
    setIsRunning(false);
    setIsUpdating(true);
    pendingUpdates.current = {};

    try {
      const result = await api.resetSimulation(simId);

      if (result.success) {
        setPlots(result.plots || []);
        if (result.parameters) {
          setCurrentParams(result.parameters);
        }
        setError(null);
        return { success: true };
      } else {
        setError(result.error || 'Reset failed');
        return { success: false, error: result.error };
      }
    } catch (err) {
      const errorMsg = err.message || 'Reset failed';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setIsUpdating(false);
    }
  }, [simId]);

  /**
   * Toggle animation (play/pause)
   */
  const toggleAnimation = useCallback(() => {
    setIsRunning(prev => !prev);
  }, []);

  /**
   * Step forward one frame (for manual navigation)
   */
  const stepForward = useCallback(async () => {
    if (isAnimatingRef.current || !mountedRef.current) return;

    isAnimatingRef.current = true;
    setIsUpdating(true);

    try {
      const result = await api.executeSimulation(simId, 'step_forward', {});

      if (!mountedRef.current) return;

      if (result.success) {
        setPlots(result.plots || []);
        if (result.parameters) {
          setCurrentParams(prev => ({ ...prev, ...result.parameters }));
        }
        if (result.metadata) {
          setMetadata(result.metadata);
        }
      }
    } catch (err) {
      console.error('Step forward failed:', err);
    } finally {
      isAnimatingRef.current = false;
      if (mountedRef.current) {
        setIsUpdating(false);
      }
    }
  }, [simId]);

  /**
   * Step backward one frame (for manual navigation)
   */
  const stepBackward = useCallback(async () => {
    if (isAnimatingRef.current || !mountedRef.current) return;

    isAnimatingRef.current = true;
    setIsUpdating(true);

    try {
      const result = await api.executeSimulation(simId, 'step_backward', {});

      if (!mountedRef.current) return;

      if (result.success) {
        setPlots(result.plots || []);
        if (result.parameters) {
          setCurrentParams(prev => ({ ...prev, ...result.parameters }));
        }
        if (result.metadata) {
          setMetadata(result.metadata);
        }
      }
    } catch (err) {
      console.error('Step backward failed:', err);
    } finally {
      isAnimatingRef.current = false;
      if (mountedRef.current) {
        setIsUpdating(false);
      }
    }
  }, [simId]);

  /**
   * Advance animation by one frame
   * Protected against overlapping calls - waits for previous frame to complete
   */
  const advanceFrame = useCallback(async () => {
    // Skip if previous frame is still processing
    if (isAnimatingRef.current || !mountedRef.current) return;

    isAnimatingRef.current = true;

    try {
      const result = await api.advanceFrame(simId);

      if (!mountedRef.current) return;

      if (result.success) {
        setPlots(result.plots || []);
        // Update metadata if present
        if (result.metadata) {
          setMetadata(result.metadata);
        }
        // Sync animation params (like time_shift) from backend
        if (result.parameters) {
          setCurrentParams(prev => ({
            ...prev,
            ...result.parameters,
          }));
        }
      }
    } catch (err) {
      console.error('Animation frame failed:', err);
    } finally {
      isAnimatingRef.current = false;
    }
  }, [simId]);

  /**
   * Handle button actions (play_pause, reset)
   */
  const handleButtonAction = useCallback((buttonName) => {
    if (buttonName === 'play_pause') {
      toggleAnimation();
    } else if (buttonName === 'reset') {
      resetToDefaults();
    }
  }, [toggleAnimation, resetToDefaults]);

  // Animation loop effect - uses setTimeout chain to prevent overlapping
  // Uses animation_speed from currentParams for speed control
  useEffect(() => {
    let timeoutId = null;
    let isActive = false;

    const runAnimationLoop = async () => {
      if (!isActive || !isRunning) return;

      await advanceFrame();

      // Schedule next frame only after current one completes
      // Use animation_speed from params (default 1.0x)
      if (isActive && isRunning) {
        const speed = currentParams.animation_speed || 1.0;
        const interval = Math.max(20, Math.floor(ANIMATION_BASE_INTERVAL / speed));
        timeoutId = setTimeout(runAnimationLoop, interval);
      }
    };

    if (isRunning) {
      isActive = true;
      // Cancel any pending debounced updates when animation starts
      if (debouncedUpdateRef.current?.cancel) {
        debouncedUpdateRef.current.cancel();
      }
      // Flush any pending updates immediately before starting animation
      const pendingKeys = Object.keys(pendingUpdates.current);
      if (pendingKeys.length > 0) {
        flushUpdates();
      }
      // Start the animation loop
      runAnimationLoop();
    }

    return () => {
      isActive = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isRunning, advanceFrame, flushUpdates, currentParams.animation_speed]);

  /**
   * Load simulation definition and initial state
   */
  useEffect(() => {
    mountedRef.current = true;

    async function loadSimulation() {
      if (!simId) {
        setError('No simulation ID provided');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Fetch simulation definition
        const simResult = await api.getSimulation(simId);

        if (!mountedRef.current) return;

        if (!simResult.success) {
          setError(simResult.error || 'Failed to load simulation');
          setIsLoading(false);
          return;
        }

        setSimulation(simResult.data);

        // Set default parameters from definition
        const defaults = simResult.data.default_params || {};
        setCurrentParams(defaults);

        // Check if this simulation has an active simulator
        if (simResult.data.has_simulator) {
          // Fetch current state (initializes simulator if needed)
          const stateResult = await api.getSimulationState(simId);

          if (!mountedRef.current) return;

          if (stateResult.success) {
            setPlots(stateResult.plots || []);
            if (stateResult.parameters) {
              setCurrentParams(stateResult.parameters);
            }
            if (stateResult.metadata) {
              console.log('[useSimulation init] Setting initial metadata, is_stable:', stateResult.metadata?.system_info?.is_stable);
              setMetadata(stateResult.metadata);
            }
          } else {
            // Still show the simulation, just no plots
            console.warn('Could not load simulation state:', stateResult.error);
          }
        }
      } catch (err) {
        if (mountedRef.current) {
          setError(err.message || 'Failed to load simulation');
        }
      } finally {
        if (mountedRef.current) {
          setIsLoading(false);
        }
      }
    }

    loadSimulation();

    return () => {
      mountedRef.current = false;
      // Reset animation refs on unmount
      isAnimatingRef.current = false;
      isFlushingRef.current = false;
    };
  }, [simId]);

  return {
    // State
    simulation,
    currentParams,
    plots,
    metadata,
    isLoading,
    isUpdating,
    error,
    isRunning,

    // Methods
    updateParam,
    updateParams,
    setParamsFromUrl,
    initializeSimulation,
    resetToDefaults,
    toggleAnimation,
    stepForward,
    stepBackward,
    handleButtonAction,

    // Utilities
    getParamDef,
    validateParam,
  };
}

export default useSimulation;
