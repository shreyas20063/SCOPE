/**
 * API Client for SCOPE Platform
 *
 * Provides methods to interact with the backend API:
 * - Get simulations list
 * - Get simulation details
 * - Execute simulation actions
 * - Update parameters
 */

import axios from 'axios';

// API Configuration
// In production (Render), VITE_API_URL points to the backend service
// In development, we use relative URL with Vite proxy
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';
const API_TIMEOUT = 30000; // 30 seconds

// Session ID — per-tab isolation so concurrent users don't share simulator state.
// sessionStorage is scoped to each browser tab, so two tabs = two sessions
// (duplicated tabs inherit a copy; see the duplicate check below).
//
// Note: `crypto.randomUUID()` requires a secure context (HTTPS or localhost).
// On plain HTTP over a LAN IP (e.g. http://10.200.240.13:8000), `crypto.randomUUID`
// is undefined and throws. The fallback below uses `crypto.getRandomValues` —
// available on every origin, secure or not — to generate a UUID v4 manually.
function generateUUID() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40; // UUID v4
    bytes[8] = (bytes[8] & 0x3f) | 0x80; // RFC 4122 variant
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  // Last-resort (Math.random — low entropy, fine for session keys on trusted WiFi).
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

const SESSION_STORAGE_KEY = 'scope_session_id';

function safeGet(storage, key) {
  try { return storage.getItem(key); } catch { return null; }
}

function safeSet(storage, key, value) {
  try { storage.setItem(key, value); } catch { /* storage unavailable */ }
}

function mintSessionId() {
  const sid = generateUUID();
  safeSet(sessionStorage, SESSION_STORAGE_KEY, sid);
  return sid;
}

let SESSION_ID = safeGet(sessionStorage, SESSION_STORAGE_KEY);
const restoredSession = !!SESSION_ID;
if (!SESSION_ID) {
  SESSION_ID = mintSessionId();
}

// Duplicated tabs — "Duplicate Tab" (and window.open with an opener) copies
// sessionStorage, so the copy would silently share the original tab's backend
// simulator instances. Each page claims its session id in localStorage
// (released on pagehide, so reloads and reopened tabs keep their session). A
// page that restores an id already claimed by another page asks over a
// BroadcastChannel whether that page is still alive; if it answers, this page
// mints a fresh id. API requests wait for that check (at most
// DUPLICATE_PROBE_MS, and only in the rare claimed-id case). A stale claim left
// by a crash or a discarded tab simply times out and the id is kept.
const SESSION_CLAIM_PREFIX = 'scope_session_claim:';
const SESSION_CHANNEL_NAME = 'scope-session';
const DUPLICATE_PROBE_MS = 150;
// One token per page load; kept on window so an HMR re-run of this module in
// the same page is not mistaken for a duplicate.
const PAGE_TOKEN = window.__scopePageToken || (window.__scopePageToken = generateUUID());

let sessionChannel = null;
try {
  sessionChannel = typeof BroadcastChannel === 'function' ? new BroadcastChannel(SESSION_CHANNEL_NAME) : null;
} catch {
  sessionChannel = null;
}

function claimSession() {
  safeSet(localStorage, SESSION_CLAIM_PREFIX + SESSION_ID, PAGE_TOKEN);
}

function releaseSession() {
  const key = SESSION_CLAIM_PREFIX + SESSION_ID;
  if (safeGet(localStorage, key) === PAGE_TOKEN) {
    try { localStorage.removeItem(key); } catch { /* storage unavailable */ }
  }
}

function reclaimAfterBfcache(e) {
  if (e.persisted) claimSession();
}

window.addEventListener('pagehide', releaseSession);
window.addEventListener('pageshow', reclaimAfterBfcache);

// Answer liveness probes for the session this page is using.
sessionChannel?.addEventListener('message', (e) => {
  const msg = e.data;
  if (msg?.type === 'probe' && msg.sid === SESSION_ID && msg.token !== PAGE_TOKEN) {
    sessionChannel.postMessage({ type: 'alive', sid: SESSION_ID, token: PAGE_TOKEN });
  }
});

const claimOwner = safeGet(localStorage, SESSION_CLAIM_PREFIX + SESSION_ID);
const possiblyDuplicated = restoredSession && claimOwner && claimOwner !== PAGE_TOKEN
  && !document.wasDiscarded && sessionChannel;

const sessionReady = possiblyDuplicated
  ? new Promise((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      sessionChannel.removeEventListener('message', onMessage);
      claimSession();
      resolve();
    };
    const onMessage = (e) => {
      const msg = e.data;
      if (msg?.type === 'alive' && msg.sid === SESSION_ID && msg.token !== PAGE_TOKEN) {
        SESSION_ID = mintSessionId();
        finish();
      }
    };
    const timer = setTimeout(finish, DUPLICATE_PROBE_MS);
    sessionChannel.addEventListener('message', onMessage);
    sessionChannel.postMessage({ type: 'probe', sid: SESSION_ID, token: PAGE_TOKEN });
  })
  : (claimSession(), Promise.resolve());

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    sessionChannel?.close();
    window.removeEventListener('pagehide', releaseSession);
    window.removeEventListener('pageshow', reclaimAfterBfcache);
  });
}

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the (possibly re-minted) session id once the duplicate check settles.
apiClient.interceptors.request.use(async (config) => {
  await sessionReady;
  config.headers.set('X-Session-ID', SESSION_ID);
  return config;
});

/**
 * Handle API errors and return structured error object
 */
function handleError(error) {
  if (error.response) {
    // Server responded with error status
    return {
      success: false,
      error: error.response.data?.error || error.response.data?.detail || 'Server error',
      details: error.response.data?.details || null,
      status: error.response.status,
    };
  } else if (error.request) {
    // Request made but no response
    return {
      success: false,
      error: 'Network error - server may be down',
      details: 'Unable to connect to the server. Please check if the backend is running.',
      status: 0,
    };
  } else {
    // Error setting up request
    return {
      success: false,
      error: error.message || 'Unknown error',
      details: null,
      status: 0,
    };
  }
}

/**
 * API Client class for simulation platform
 */
class ApiClient {
  /**
   * Get all simulations
   * @param {string} [category] - Optional category filter
   * @returns {Promise<{success: boolean, data?: Array, error?: string}>}
   */
  async getSimulations(category = null) {
    try {
      const params = category ? { category } : {};
      const response = await apiClient.get('/simulations', { params });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Get a specific simulation by ID
   * @param {string} simId - Simulation ID
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   */
  async getSimulation(simId) {
    try {
      const response = await apiClient.get(`/simulations/${simId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Get simulation state (current parameters and plots)
   * @param {string} simId - Simulation ID
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   */
  async getSimulationState(simId) {
    try {
      const response = await apiClient.get(`/simulations/${simId}/state`);
      return {
        success: true,
        data: response.data.data,
        plots: response.data.data?.plots || [],
        parameters: response.data.data?.parameters || {},
        metadata: response.data.data?.metadata || null,
      };
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Execute a simulation action
   * @param {string} simId - Simulation ID
   * @param {string} action - Action type: "init" | "update" | "run" | "reset"
   * @param {Object} params - Parameters for the action
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async executeSimulation(simId, action, params = {}) {
    try {
      const response = await apiClient.post(`/simulations/${simId}/execute`, {
        action,
        params,
      });

      if (response.data.success) {
        return {
          success: true,
          data: response.data.data,
          plots: response.data.data?.plots || [],
          parameters: response.data.data?.parameters || {},
          metadata: response.data.data?.metadata || null,
        };
      } else {
        return {
          success: false,
          error: response.data.error || 'Execution failed',
          details: response.data.details,
        };
      }
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Update simulation parameters (convenience method)
   * @param {string} simId - Simulation ID
   * @param {Object} params - Parameters to update {paramName: value, ...}
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async updateParameters(simId, params) {
    try {
      const response = await apiClient.post(`/simulations/${simId}/update`, {
        params,
      });

      if (response.data.success) {
        return {
          success: true,
          data: response.data.data,
          plots: response.data.data?.plots || [],
          parameters: response.data.data?.parameters || {},
          metadata: response.data.data?.metadata || null,
        };
      } else {
        return {
          success: false,
          error: response.data.error || 'Update failed',
          details: response.data.details,
        };
      }
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Update a single parameter (convenience method)
   * @param {string} simId - Simulation ID
   * @param {string} paramName - Parameter name
   * @param {any} value - New parameter value
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async updateParameter(simId, paramName, value) {
    return this.updateParameters(simId, { [paramName]: value });
  }

  /**
   * Initialize simulation with parameters
   * @param {string} simId - Simulation ID
   * @param {Object} params - Initial parameters
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async initializeSimulation(simId, params = {}) {
    return this.executeSimulation(simId, 'init', params);
  }

  /**
   * Reset simulation to default parameters
   * @param {string} simId - Simulation ID
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async resetSimulation(simId) {
    return this.executeSimulation(simId, 'reset', {});
  }

  /**
   * Run simulation with all provided parameters
   * @param {string} simId - Simulation ID
   * @param {Object} params - All parameters
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async runSimulation(simId, params) {
    return this.executeSimulation(simId, 'run', params);
  }

  /**
   * Advance animation by one frame (for animated simulations)
   * @param {string} simId - Simulation ID
   * @returns {Promise<{success: boolean, data?: Object, plots?: Array, error?: string}>}
   */
  async advanceFrame(simId) {
    return this.executeSimulation(simId, 'advance', {});
  }

  /**
   * Get all categories
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   */
  async getCategories() {
    try {
      const response = await apiClient.get('/categories');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Health check
   * @returns {Promise<{success: boolean, status?: string, error?: string}>}
   */
  async healthCheck() {
    try {
      // Health endpoint is at root level, not under /api
      const baseUrl = import.meta.env.VITE_API_URL || '';
      const response = await axios.get(`${baseUrl}/health`, { timeout: 5000 });
      return {
        success: true,
        status: response.data.status,
      };
    } catch (error) {
      return handleError(error);
    }
  }

  /**
   * Validate and enrich hub slot data via backend
   * @param {string} slot - Slot name (control, signal, circuit, optics)
   * @param {Object} data - Slot data to validate
   * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
   */
  async validateHubData(slot, data) {
    try {
      const response = await apiClient.post('/hub/validate', { slot, data }, { timeout: 5000 });
      return {
        success: response.data.success,
        data: response.data.data || null,
        error: response.data.error || null,
      };
    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        return { success: false, error: 'Validation timed out', data: null };
      }
      return handleError(error);
    }
  }
}

// Export singleton instance
const api = new ApiClient();
export default api;

// Also export the class for testing
export { ApiClient };

// Export session ID for WebSocket connections (can't use custom headers with WebSocket API)
export { SESSION_ID };
