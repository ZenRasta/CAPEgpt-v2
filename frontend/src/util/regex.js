/**
 * Regex utility functions for safely handling dynamic patterns
 */

/**
 * Escapes special regex characters in a string to make it safe for use in RegExp constructor
 * 
 * This is particularly important when using OCR text that may contain LaTeX symbols
 * like \int, \sum, {}, [], etc. which have special meaning in regex.
 * 
 * @param {string} str - The string to escape
 * @returns {string} The escaped string safe for regex use
 */
export const escapeRegex = (str) => {
  if (typeof str !== 'string') {
    return '';
  }
  
  // Escape all special regex characters
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

/**
 * Safely creates a RegExp from potentially unsafe text
 * 
 * @param {string} pattern - The pattern to create regex from
 * @param {string} flags - Optional regex flags (default: 'i')
 * @returns {RegExp|null} The created RegExp or null if invalid
 */
export const safeRegExp = (pattern, flags = 'i') => {
  try {
    if (!pattern || typeof pattern !== 'string') {
      return null;
    }
    
    const escapedPattern = escapeRegex(pattern.trim());
    return new RegExp(escapedPattern, flags);
  } catch (error) {
    console.warn('Failed to create regex from pattern:', pattern, error);
    return null;
  }
};