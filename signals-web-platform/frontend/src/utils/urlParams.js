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
    if (value !== undefined && value !== null) {
      // Handle different types
      if (typeof value === 'boolean') {
        searchParams.set(key, value ? '1' : '0');
      } else if (typeof value === 'number') {
        // Round to 4 decimal places to avoid floating point issues
        searchParams.set(key, String(Math.round(value * 10000) / 10000));
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
