export function sanitizeAIError(err) {
  let errorMessage = 'Failed to get AI analysis';
  const original = err && err.message ? String(err.message) : '';
  if (original) {
    if (/bad escape|invalid regular expression/i.test(original)) {
      errorMessage = 'Unable to parse OCR output. Please ensure OCR services are properly configured.';
    } else {
      try {
        errorMessage = original
          .replace(/\\/g, '\\\\')
          .replace(/"/g, '\\"')
          .replace(/'/g, "\\'");
      } catch (e) {
        console.error('Error sanitizing AI analysis message:', e);
        errorMessage = 'Failed to get AI analysis (Error details unavailable)';
      }
    }
  }
  return errorMessage;
}
