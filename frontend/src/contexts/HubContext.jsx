import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react';
import api from '../services/api';

const STORAGE_KEY = 'systemHub';
const EMPTY_HUB = { control: null, signal: null, circuit: null, optics: null };

/**
 * Deep merge two objects. Arrays and null values are replaced, not merged.
 */
function deepMerge(target, source) {
  if (!target) return { ...source };
  if (!source) return { ...target };
  const result = { ...target };
  for (const key of Object.keys(source)) {
    if (source[key] !== null && typeof source[key] === 'object' && !Array.isArray(source[key])
        && typeof result[key] === 'object' && !Array.isArray(result[key]) && result[key] !== null) {
      result[key] = deepMerge(result[key], source[key]);
    } else {
      result[key] = source[key];
    }
  }
  return result;
}

/**
 * Load hub state from localStorage, falling back to empty slots.
 */
function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...EMPTY_HUB, ...parsed };
    }
  } catch {
    // Corrupt data — start fresh
  }
  return { ...EMPTY_HUB };
}

/**
 * Persist hub state to localStorage.
 */
function saveToStorage(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}

const HubContext = createContext(null);

export function HubProvider({ children }) {
  const [hubState, setHubState] = useState(loadFromStorage);
  const subscribersRef = useRef({
    control: new Set(),
    signal: new Set(),
    circuit: new Set(),
    optics: new Set(),
  });

  // Cross-tab sync via storage events
  useEffect(() => {
    function handleStorageEvent(e) {
      if (e.key === STORAGE_KEY) {
        const newState = e.newValue ? JSON.parse(e.newValue) : { ...EMPTY_HUB };
        setHubState({ ...EMPTY_HUB, ...newState });
        // Notify all subscribers for all slots since we don't know which changed
        for (const slotName of Object.keys(subscribersRef.current)) {
          for (const cb of subscribersRef.current[slotName]) {
            try { cb(newState[slotName] || null); } catch { /* ignore */ }
          }
        }
      }
    }
    window.addEventListener('storage', handleStorageEvent);
    return () => window.removeEventListener('storage', handleStorageEvent);
  }, []);

  /**
   * Notify subscribers for a specific slot.
   */
  const notifySubscribers = useCallback((slotName, data) => {
    const subs = subscribersRef.current[slotName];
    if (subs) {
      for (const cb of subs) {
        try { cb(data); } catch { /* ignore */ }
      }
    }
  }, []);

  /**
   * Push data into a hub slot. Validates via backend for the control slot.
   * Deep-merges enriched data into the existing slot (not replace).
   */
  const pushToSlot = useCallback(async (slotName, data, simId) => {
    if (!EMPTY_HUB.hasOwnProperty(slotName)) {
      console.warn(`[Hub] Unknown slot: ${slotName}`);
      return;
    }

    let enrichedData = data;

    // Validate via backend for the control slot
    if (slotName === 'control') {
      const result = await api.validateHubData(slotName, data);
      if (result.success && result.data) {
        enrichedData = result.data;
      }
      // If validation fails, use raw data as fallback
    }

    // Add metadata
    enrichedData = {
      ...enrichedData,
      _meta: { pushed_by: simId, timestamp: Date.now() },
    };

    setHubState(prev => {
      const currentSlot = prev[slotName];

      // Stale controller detection: if plant TF changed and controller exists
      let merged = deepMerge(currentSlot, enrichedData);
      if (slotName === 'control' && currentSlot) {
        const oldPlant = currentSlot.plant;
        const newPlant = enrichedData.plant;
        if (oldPlant && newPlant && currentSlot.controller) {
          // Check if plant TF actually changed
          const plantChanged =
            JSON.stringify(oldPlant.numerator) !== JSON.stringify(newPlant.numerator) ||
            JSON.stringify(oldPlant.denominator) !== JSON.stringify(newPlant.denominator);
          if (plantChanged) {
            merged = {
              ...merged,
              controller: { ...merged.controller, stale: true },
            };
          }
        }
      }

      const nextState = { ...prev, [slotName]: merged };
      saveToStorage(nextState);
      notifySubscribers(slotName, merged);
      return nextState;
    });
  }, [notifySubscribers]);

  /**
   * Get current slot data (instant read from state).
   */
  const getSlot = useCallback((slotName) => {
    return hubState[slotName] || null;
  }, [hubState]);

  /**
   * Subscribe to changes on a specific slot. Returns an unsubscribe function.
   */
  const subscribe = useCallback((slotName, callback) => {
    if (!subscribersRef.current[slotName]) {
      subscribersRef.current[slotName] = new Set();
    }
    subscribersRef.current[slotName].add(callback);
    return () => {
      subscribersRef.current[slotName].delete(callback);
    };
  }, []);

  /**
   * Clear a specific slot.
   */
  const clearSlot = useCallback((slotName) => {
    setHubState(prev => {
      const nextState = { ...prev, [slotName]: null };
      saveToStorage(nextState);
      notifySubscribers(slotName, null);
      return nextState;
    });
  }, [notifySubscribers]);

  /**
   * Clear all slots.
   */
  const clearAll = useCallback(() => {
    const nextState = { ...EMPTY_HUB };
    setHubState(nextState);
    saveToStorage(nextState);
    for (const slotName of Object.keys(subscribersRef.current)) {
      notifySubscribers(slotName, null);
    }
  }, [notifySubscribers]);

  const value = {
    hubState,
    pushToSlot,
    getSlot,
    subscribe,
    clearSlot,
    clearAll,
  };

  return (
    <HubContext.Provider value={value}>
      {children}
    </HubContext.Provider>
  );
}

export function useHubContext() {
  const context = useContext(HubContext);
  if (!context) {
    throw new Error('useHubContext must be used within a HubProvider');
  }
  return context;
}

export default HubContext;
