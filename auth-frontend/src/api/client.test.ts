/**
 * Unit tests for src/api/client.ts
 * Test runner: Vitest (most common for Vite/TypeScript frontend projects)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError } from './types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeResponse(
  status: number,
  body: unknown,
  ok?: boolean,
): Response {
  const isOk = ok !== undefined ? ok : status >= 200 && status < 300;
  return {
    status,
    ok: isOk,
    json: () => Promise.resolve(body),
    headers: new Headers(),
    redirected: false,
    statusText: '',
    type: 'basic',
    url: '',
    clone: () => makeResponse(status, body, isOk),
    body: null,
    bodyUsed: false,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(''),
  } as unknown as Response;
}

function makeResponseThrowingJson(status: number, ok?: boolean): Response {
  const isOk = ok !== undefined ? ok : status >= 200 && status < 300;
  return {
    status,
    ok: isOk,
    json: () => Promise.reject(new SyntaxError('Unexpected token')),
  } as unknown as Response;
}

// ---------------------------------------------------------------------------
// Module re-import helper so module-level state is reset between test groups
// ---------------------------------------------------------------------------

async function importClient() {
  // Dynamic import to get a fresh module (vitest resets modules if resetModules is used)
  const mod = await import('./client');
  return mod;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('apiFetch', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    // Reset module state by re-importing; we mock fetch globally
    vi.resetModules();
    localStorage.clear();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
    localStorage.clear();
  });

  // -------------------------------------------------------------------------
  // Happy-path: successful request
  // -------------------------------------------------------------------------

  it('returns parsed JSON on a successful 200 response', async () => {
    const responseBody = { id: '1', name: 'Alice' };
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(200, responseBody));

    const { apiFetch } = await importClient();
    const result = await apiFetch('/users/1');

    expect(result).toEqual(responseBody);
  });

  it('sends Content-Type application/json header', async () => {
    const fetchMock = vi.fn().mockResolvedValue(makeResponse(200, {}));
    globalThis.fetch = fetchMock;

    const { apiFetch } = await importClient();
    await apiFetch('/test');

    const calledHeaders = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(calledHeaders['Content-Type']).toBe('application/json');
  });

  it('adds Authorization header when access_token exists in localStorage', async () => {
    localStorage.setItem('access_token', 'my-token');
    const fetchMock = vi.fn().mockResolvedValue(makeResponse(200, {}));
    globalThis.fetch = fetchMock;

    const { apiFetch } = await importClient();
    await apiFetch('/secure');

    const calledHeaders = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(calledHeaders['Authorization']).toBe('Bearer my-token');
  });

  it('does NOT add Authorization header when no token in localStorage', async () => {
    const fetchMock = vi.fn().mockResolvedValue(makeResponse(200, {}));
    globalThis.fetch = fetchMock;

    const { apiFetch } = await importClient();
    await apiFetch('/public');

    const calledHeaders = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(calledHeaders['Authorization']).toBeUndefined();
  });

  it('includes credentials: include on every request', async () => {
    const fetchMock = vi.fn().mockResolvedValue(makeResponse(200, {}));
    globalThis.fetch = fetchMock;

    const { apiFetch } = await importClient();
    await apiFetch('/secure');

    expect(fetchMock.mock.calls[0][1].credentials).toBe('include');
  });

  it('merges caller-supplied headers with defaults', async () => {
    const fetchMock = vi.fn().mockResolvedValue(makeResponse(200, {}));
    globalThis.fetch = fetchMock;

    const { apiFetch } = await importClient();
    await apiFetch('/test', { headers: { 'X-Custom': 'yes' } });

    const calledHeaders = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(calledHeaders['X-Custom']).toBe('yes');
    expect(calledHeaders['Content-Type']).toBe('application/json');
  });

  // -------------------------------------------------------------------------
  // 204 No Content
  // -------------------------------------------------------------------------

  it('returns undefined for 204 No Content responses', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(204, null));

    const { apiFetch } = await importClient();
    const result = await apiFetch('/delete-something');

    expect(result).toBeUndefined();
  });

  // -------------------------------------------------------------------------
  // Non-2xx errors (non-401)
  // -------------------------------------------------------------------------

  it('throws ApiError with structured body on 400 response', async () => {
    const errorBody = {
      error: { code: 'VALIDATION_ERROR', message: 'Bad input', details: { email: ['required'] } },
    };
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(400, errorBody));

    const { apiFetch } = await importClient();

    await expect(apiFetch('/register')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return (
        err instanceof ApiError &&
        err.status === 400 &&
        err.code === 'VALIDATION_ERROR' &&
        err.message === 'Bad input' &&
        Array.isArray(err.details['email'])
      );
    });
  });

  it('throws ApiError with fallback values when error body is missing error key', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(500, { something: 'else' }));

    const { apiFetch } = await importClient();

    await expect(apiFetch('/crash')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return (
        err instanceof ApiError &&
        err.status === 500 &&
        err.code === 'UNKNOWN_ERROR' &&
        err.message === 'Request failed with status 500'
      );
    });
  });

  it('throws ApiError when response JSON parsing fails', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponseThrowingJson(500));

    const { apiFetch } = await importClient();

    await expect(apiFetch('/crash')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return (
        err instanceof ApiError &&
        err.status === 500 &&
        err.code === 'UNKNOWN_ERROR'
      );
    });
  });

  it('throws ApiError when body is null', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(503, null));

    const { apiFetch } = await importClient();

    await expect(apiFetch('/unavailable')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return err instanceof ApiError && err.status === 503 && err.code === 'UNKNOWN_ERROR';
    });
  });

  // -------------------------------------------------------------------------
  // 401 handling — silent token refresh succeeds
  // -------------------------------------------------------------------------

  it('retries with new token after successful silent refresh on 401', async () => {
    const successBody = { data: 'secret' };
    let callCount = 0;

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if ((url as string).includes('/auth/refresh')) {
        return Promise.resolve(makeResponse(200, { access_token: 'new-token' }));
      }
      callCount += 1;
      if (callCount === 1) {
        // First call: simulate 401
        return Promise.resolve(makeResponse(401, { error: { code: 'UNAUTHORIZED', message: 'expired', details: {} } }));
      }
      // Second call (retry with new token): success
      return Promise.resolve(makeResponse(200, successBody));
    });

    const { apiFetch } = await importClient();
    const result = await apiFetch<{ data: string }>('/secure-data');

    expect(result).toEqual(successBody);
    expect(localStorage.getItem('access_token')).toBe('new-token');
  });

  // -------------------------------------------------------------------------
  // 401 handling — silent token refresh fails
  // -------------------------------------------------------------------------

  it('throws UNAUTHORIZED ApiError and clears token when refresh fails', async () => {
    localStorage.setItem('access_token', 'stale-token');

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if ((url as string).includes('/auth/refresh')) {
        return Promise.resolve(makeResponse(401, null));
      }
      return Promise.resolve(makeResponse(401, { error: { code: 'UNAUTHORIZED', message: 'expired', details: {} } }));
    });

    const { apiFetch } = await importClient();

    await expect(apiFetch('/protected')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return (
        err instanceof ApiError &&
        err.status === 401 &&
        err.code === 'UNAUTHORIZED'
      );
    });

    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('throws UNAUTHORIZED ApiError when refresh endpoint throws a network error', async () => {
    localStorage.setItem('access_token', 'stale-token');

    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if ((url as string).includes('/auth/refresh')) {
        return Promise.reject(new Error('Network failure'));
      }
      return Promise.resolve(makeResponse(401, {}));
    });

    const { apiFetch } = await importClient();

    await expect(apiFetch('/protected')).rejects.toBeInstanceOf(ApiError);
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  // -------------------------------------------------------------------------
  // buildApiError edge cases
  // -------------------------------------------------------------------------

  it('uses fallback code/message when error object fields are wrong type', async () => {
    const badErrorBody = {
      error: { code: 123, message: null, details: {} },
    };
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(422, badErrorBody));

    const { apiFetch } = await importClient();

    await expect(apiFetch('/validate')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return (
        err instanceof ApiError &&
        err.status === 422 &&
        err.code === 'UNKNOWN_ERROR' &&
        err.message === 'Request failed with status 422'
      );
    });
  });

  it('uses empty details object when error.details is missing', async () => {
    const errorBody = {
      error: { code: 'NOT_FOUND', message: 'Resource not found' },
    };
    globalThis.fetch = vi.fn().mockResolvedValue(makeResponse(404, errorBody));

    const { apiFetch } = await importClient();

    await expect(apiFetch('/missing')).rejects.toSatisfy((e: unknown) => {
      const err = e as ApiError;
      return (
        err instanceof ApiError &&
        err.status === 404 &&
        err.code === 'NOT_FOUND' &&
        typeof err.details === 'object' &&
        Object.keys(err.details).length === 0
      );
    });
  });
});

// ---------------------------------------------------------------------------
// ApiError class (types.ts)
// ---------------------------------------------------------------------------

describe('ApiError', () => {
  it('sets all properties correctly', () => {
    const err = new ApiError(403, 'FORBIDDEN', 'Access denied', { field: ['required'] });

    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(403);
    expect(err.code).toBe('FORBIDDEN');
    expect(err.message).toBe('Access denied');
    expect(err.details).toEqual({ field: ['required'] });
    expect(err.name).toBe('ApiError');
  });

  it('works with empty details', () => {
    const err = new ApiError(500, 'SERVER_ERROR', 'Oops', {});
    expect(err.details).toEqual({});
  });
});
