// Setup Jest per testing
import '@testing-library/jest-dom';

// Mock fetch for testing environment
global.fetch = jest.fn();

// Console warnings suppression for cleaner test output
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: An update to') &&
      args[0].includes('act(...)')
    ) {
      return; // Suppress act() warnings during testing
    }
    originalError.call(console, ...args);
  };

  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('React Router Future Flag Warning') ||
       args[0].includes('validateDOMNesting'))
    ) {
      return; // Suppress React Router and DOM nesting warnings
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// MSW Setup per test che richiedono mock API (disabilitato per ora)
// import { server } from './__mocks__/server';

// Setup MSW server (da abilitare quando necessario)
/*
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
*/

// Mock per window.matchMedia (non supportato in jsdom)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock per ResizeObserver (non supportato in jsdom)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock per IntersectionObserver (non supportato in jsdom)
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Setup per Environment Variables di test
process.env.NODE_ENV = 'test';
process.env.REACT_APP_API_BASE_URL = 'http://localhost:8000';
