/**
 * API Client for Signals & Systems Simulation Platform
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
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
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
}

// Export singleton instance
const api = new ApiClient();
export default api;

// Also export the class for testing
export { ApiClient };
