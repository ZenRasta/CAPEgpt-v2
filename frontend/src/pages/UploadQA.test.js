import assert from 'assert';
import { sanitizeAIError } from './uploadQaError.js';

const fakeError = new Error('Invalid regular expression: /(?:a\\)/: bad escape');
const message = sanitizeAIError(fakeError);

assert.strictEqual(
  message,
  'Unable to parse OCR output. Please ensure OCR services are properly configured.'
);

console.log('UploadQA error handler tests passed');
