/**
 * useWebSocketSimulation Hook
 *
 * Real-time simulation updates via WebSocket.
 * Provides instant parameter updates without HTTP overhead.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

const WS_BASE_URL = 'ws://localhost:8000/api/v1';

/**
 * Custom hook for real-time simulation via WebSocket
 * @param {string} simId - Simulation ID
 * @returns {Object} Simulation state and methods
 */
export function useWebSocketSimulation(simId) {
  // State
  const [simulation, setSimulation] = useState(null);
  const [currentParams, setCurrentParams] = useState({});
  const [plots, setPlots] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  // Refs
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!simId) return;

    const wsUrl = `${WS_BASE_URL}/simulations/${simId}/ws`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        setIsLoading(false);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket received:', data);

          if (data.success) {
            if (data.plots) {
              console.log('Setting plots:', data.plots.length, 'plots');
              setPlots(data.plots);
            }
            if (data.parameters) {
              setCurrentParams(data.parameters);
            }
            setError(null);
          } else {
            console.error('WebSocket error:', data.error);
            setError(data.error || 'WebSocket error');
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (e) => {
        console.error('WebSocket error:', e);
        setError('WebSocket connection error');
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Attempt reconnect after 2 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (wsRef.current === ws) {
            connect();
          }
        }, 2000);
      };

      wsRef.current = ws;
    } catch (e) {
      setError('Failed to create WebSocket connection');
    }
  }, [simId]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  /**
   * Send message via WebSocket
   */
  const send = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  /**
   * Update a single parameter - instant via WebSocket
   */
  const updateParam = useCallback((paramName, value) => {
    // Update local state immediately for responsive UI
    setCurrentParams(prev => ({
      ...prev,
      [paramName]: value,
    }));

    // Send via WebSocket (no debounce needed - it's fast!)
    send({
      action: 'update',
      params: { [paramName]: value }
    });
  }, [send]);

  /**
   * Update multiple parameters at once
   */
  const updateParams = useCallback((params) => {
    // Update local state immediately
    setCurrentParams(prev => ({
      ...prev,
      ...params,
    }));

    // Send via WebSocket
    send({
      action: 'update',
      params
    });
  }, [send]);

  /**
   * Reset to default parameters
   */
  const resetToDefaults = useCallback(() => {
    send({ action: 'reset' });
  }, [send]);

  /**
   * Load simulation definition and connect WebSocket
   */
  useEffect(() => {
    let isMounted = true;

    async function loadSimulation() {
      if (!simId) {
        setError('No simulation ID provided');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Fetch simulation definition via HTTP (one-time)
        const simResult = await api.getSimulation(simId);

        if (!isMounted) return;

        if (!simResult.success) {
          setError(simResult.error || 'Failed to load simulation');
          setIsLoading(false);
          return;
        }

        setSimulation(simResult.data);

        // Set default parameters from definition
        const defaults = simResult.data.default_params || {};
        setCurrentParams(defaults);

        // Connect WebSocket for real-time updates
        connect();

      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load simulation');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadSimulation();

    return () => {
      isMounted = false;
      disconnect();
    };
  }, [simId, connect, disconnect]);

  return {
    // State
    simulation,
    currentParams,
    plots,
    isLoading,
    isUpdating: false, // WebSocket is always ready
    isConnected,
    error,

    // Methods
    updateParam,
    updateParams,
    resetToDefaults,
  };
}

export default useWebSocketSimulation;
