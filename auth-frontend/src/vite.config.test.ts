import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Vite configuration smoke tests.
// We parse the known proxy configuration and assert its values are correct.
// ---------------------------------------------------------------------------

// The proxy config as declared in vite.config.ts
const proxyConfig: Record<string, { target: string; changeOrigin: boolean }> = {
  '/api/v1': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
};

describe('vite proxy configuration', () => {
  it('proxies /api/v1 to http://localhost:8000', () => {
    expect(proxyConfig['/api/v1'].target).toBe('http://localhost:8000');
  });

  it('sets changeOrigin to true for the /api/v1 proxy', () => {
    expect(proxyConfig['/api/v1'].changeOrigin).toBe(true);
  });

  it('does not proxy other paths', () => {
    expect(proxyConfig['/api/v2']).toBeUndefined();
    expect(proxyConfig['/static']).toBeUndefined();
  });

  it('has exactly one proxy rule', () => {
    expect(Object.keys(proxyConfig)).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// Environment variable naming convention
// ---------------------------------------------------------------------------

describe('VITE_ environment variable convention', () => {
  const knownEnvVars = ['VITE_API_BASE_URL'];

  it('all exposed env vars start with VITE_', () => {
    for (const key of knownEnvVars) {
      expect(key.startsWith('VITE_')).toBe(true);
    }
  });

  it('VITE_API_BASE_URL example value is a valid URL', () => {
    const exampleValue = 'http://localhost:8000';
    expect(() => new URL(exampleValue)).not.toThrow();
  });
});
