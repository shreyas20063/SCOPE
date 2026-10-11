/**
 * URL Parameters Utility
 *
 * Encode/decode simulation parameters in URL for sharing.
 */

/**
 * Encode parameters to URL search string
 * @param {Object} params - Parameters to encode
 * @returns {string} URL search string (e.g., "?frequency=100&amplitude=5")
 */
export function encodeParams(params) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    // Objects/arrays (backend-internal state) cannot round-trip through a
    // query string, so leave them out rather than emitting "[object Object]".
    if (value !== undefined && value !== null && typeof value !== 'object') {
      // Handle different types
      if (typeof value === 'boolean') {
        searchParams.set(key, value ? '1' : '0');
      } else if (typeof value === 'number') {
        // Trim float noise (0.30000000000000004) without the absolute
        // rounding that would collapse small values such as 1e-5 to 0.
        if (Number.isFinite(value)) {
          searchParams.set(key, String(Number(value.toPrecision(12))));
        }
      } else {
        searchParams.set(key, String(value));
      }
    }
  });

  const result = searchParams.toString();
  return result ? `?${result}` : '';
}

/**
 * Decode URL search string to parameters
 * @param {string} search - URL search string
 * @param {Object} defaults - Default parameter values with types
 * @returns {Object} Decoded parameters
 */
export function decodeParams(search, defaults = {}) {
  const searchParams = new URLSearchParams(search);
  const result = {};

  searchParams.forEach((value, key) => {
    if (defaults.hasOwnProperty(key)) {
      const defaultValue = defaults[key];

      // Parse based on default value type
      if (typeof defaultValue === 'boolean') {
        result[key] = value === '1' || value === 'true';
      } else if (typeof defaultValue === 'number') {
        const parsed = parseFloat(value);
        if (!isNaN(parsed)) {
          result[key] = parsed;
        }
      } else {
        result[key] = value;
      }
    }
  });

  return result;
}

const NUMERIC_CONTROL_TYPES = new Set(['slider', 'number', 'number_input']);
const CHOICE_CONTROL_TYPES = new Set(['select', 'dropdown', 'radio']);
const TEXT_CONTROL_TYPES = new Set(['expression', 'text', 'text_input', 'textarea']);
const MAX_TEXT_PARAM_LENGTH = 2000;

/**
 * Decode URL search string against a simulation's catalog controls.
 *
 * Only keys that name a catalog control (`control.name`) are accepted, and each
 * value is validated against that control: sliders are parsed and clamped to
 * [min, max], selects must match one of their options (the option's own value
 * is returned so numeric option values keep their type), checkboxes must be a
 * boolean literal, and expressions pass through as strings. Buttons and
 * unknown keys are ignored. Keys are returned in URL order, which is the
 * order the backend reported its parameters when the link was shared.
 *
 * @param {string} search - URL search string
 * @param {Array<Object>} controls - Catalog control definitions
 * @returns {Object} Validated parameters, keyed by control name
 */
export function decodeParamsForControls(search, controls = []) {
  const byName = new Map();
  controls.forEach(control => {
    if (control?.name) byName.set(control.name, control);
  });

  const result = {};
  new URLSearchParams(search).forEach((raw, key) => {
    const control = byName.get(key);
    if (!control) return;

    if (NUMERIC_CONTROL_TYPES.has(control.type)) {
      let value = parseFloat(raw);
      if (!Number.isFinite(value)) return;
      if (typeof control.min === 'number') value = Math.max(control.min, value);
      if (typeof control.max === 'number') value = Math.min(control.max, value);
      result[key] = value;
    } else if (CHOICE_CONTROL_TYPES.has(control.type)) {
      const match = (control.options || [])
        .map(opt => (opt !== null && typeof opt === 'object' ? opt.value : opt))
        .find(value => String(value) === raw);
      if (match !== undefined) result[key] = match;
    } else if (control.type === 'checkbox') {
      if (raw === '1' || raw === 'true') result[key] = true;
      else if (raw === '0' || raw === 'false') result[key] = false;
    } else if (TEXT_CONTROL_TYPES.has(control.type)) {
      if (raw.length <= MAX_TEXT_PARAM_LENGTH) result[key] = raw;
    }
  });

  return result;
}

/**
 * Get shareable URL for current simulation state
 * @param {string} baseUrl - Base URL
 * @param {Object} params - Current parameters
 * @returns {string} Full shareable URL
 */
export function getShareableUrl(baseUrl, params) {
  const paramString = encodeParams(params);
  return `${baseUrl}${paramString}`;
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return false;
  }
}
