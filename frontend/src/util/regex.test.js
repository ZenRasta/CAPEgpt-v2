import assert from 'assert';
import { escapeRegex, safeRegExp } from './regex.js';

const sample = '\\int_0^1 \\sqrt{x} dx';

// escapeRegex should escape special characters
const escaped = escapeRegex(sample);
const manualRegex = new RegExp(escaped);
assert(manualRegex.test(sample));

// safeRegExp should return a usable RegExp object
const safe = safeRegExp(sample);
assert(safe && safe.test(sample));

console.log('regex util tests passed');
