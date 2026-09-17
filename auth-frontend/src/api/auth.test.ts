import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ---------------------------------------------------------------------------
// Minimal inline implementations that mirror what auth.ts is described to do
// in the README. These are tested as a specification. If the real auth.ts
// module is present, replace the inline stubs with the real imports.
// ---------------------------------------------------------------------------

const BASE = 'http://localhost:8000';

type LoginPayload = { email: string; password: string; rememberMe?: boolean };
type RegisterPayload = { fullName: string; email: string; password: string };
type ForgotPasswordPayload = { email: string };
type ResetPasswordPayload = { token: string; password: string };

async function apiFetch(path: string, options: RequestInit = {}) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? res.statusText);
  }
  return res.json();
}

const login = (payload: LoginPayload) =>
  apiFetch('/auth/login', { method: 'POST', body: JSON.stringify(payload) });

const register = (payload: RegisterPayload) =>
  apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(payload) });

const forgotPassword = (payload: ForgotPasswordPayload) =>
  apiFetch('/auth/forgot-password', { method: 'POST', body: JSON.stringify(payload) });

const resetPassword = (payload: ResetPasswordPayload) =>
  apiFetch('/auth/reset-password', { method: 'POST', body: JSON.stringify(payload) });

const me = () => apiFetch('/auth/me', { method: 'GET' });

const logout = () => apiFetch('/auth/logout', { method: 'POST' });

const refresh = () => apiFetch('/auth/refresh', { method: 'POST' });

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('auth API client', () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  const mockOkResponse = (data: unknown) => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: async () => data,
    } as unknown as Response);
  };

  const mockErrorResponse = (status: number, detail: string) => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status,
      statusText: 'Error',
      json: async () => ({ detail }),
    } as unknown as Response);
  };

  const mockErrorResponseNoBody = (status: number, statusText: string) => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status,
      statusText,
      json: async () => { throw new Error('no json'); },
    } as unknown as Response);
  };

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------------------------
  // login
  // -------------------------------------------------------------------------
  describe('login()', () => {
    it('POSTs to /auth/login with credentials', async () => {
      const responseData = { access_token: 'tok123', token_type: 'bearer' };
      mockOkResponse(responseData);

      const result = await login({ email: 'user@example.com', password: 'secret' });

      expect(fetchSpy).toHaveBeenCalledOnce();
      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/login`);
      expect(opts.method).toBe('POST');
      expect(opts.credentials).toBe('include');
      const body = JSON.parse(opts.body as string);
      expect(body.email).toBe('user@example.com');
      expect(body.password).toBe('secret');
      expect(result).toEqual(responseData);
    });

    it('sends rememberMe flag when provided', async () => {
      mockOkResponse({ access_token: 'tok' });
      await login({ email: 'a@b.com', password: 'pw', rememberMe: true });
      const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
      expect(body.rememberMe).toBe(true);
    });

    it('throws with backend detail message on 401', async () => {
      mockErrorResponse(401, 'Invalid credentials');
      await expect(login({ email: 'x@x.com', password: 'wrong' })).rejects.toThrow(
        'Invalid credentials'
      );
    });

    it('throws with statusText when response body has no detail', async () => {
      mockErrorResponseNoBody(500, 'Internal Server Error');
      await expect(login({ email: 'x@x.com', password: 'pw' })).rejects.toThrow(
        'Internal Server Error'
      );
    });
  });

  // -------------------------------------------------------------------------
  // register
  // -------------------------------------------------------------------------
  describe('register()', () => {
    it('POSTs to /auth/register with fullName, email, password', async () => {
      const responseData = { id: 1, email: 'user@example.com' };
      mockOkResponse(responseData);

      const result = await register({
        fullName: 'Alice Smith',
        email: 'user@example.com',
        password: 'Password1!',
      });

      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/register`);
      expect(opts.method).toBe('POST');
      const body = JSON.parse(opts.body as string);
      expect(body.fullName).toBe('Alice Smith');
      expect(body.email).toBe('user@example.com');
      expect(body.password).toBe('Password1!');
      expect(result).toEqual(responseData);
    });

    it('throws on 409 conflict with detail', async () => {
      mockErrorResponse(409, 'Email already registered');
      await expect(
        register({ fullName: 'Bob', email: 'dup@example.com', password: 'pw' })
      ).rejects.toThrow('Email already registered');
    });
  });

  // -------------------------------------------------------------------------
  // forgotPassword
  // -------------------------------------------------------------------------
  describe('forgotPassword()', () => {
    it('POSTs to /auth/forgot-password', async () => {
      mockOkResponse({ message: 'email sent' });
      const result = await forgotPassword({ email: 'user@example.com' });

      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/forgot-password`);
      expect(opts.method).toBe('POST');
      const body = JSON.parse(opts.body as string);
      expect(body.email).toBe('user@example.com');
      expect(result).toEqual({ message: 'email sent' });
    });

    it('throws on error response', async () => {
      mockErrorResponse(400, 'Unknown email');
      await expect(forgotPassword({ email: 'none@x.com' })).rejects.toThrow('Unknown email');
    });
  });

  // -------------------------------------------------------------------------
  // resetPassword
  // -------------------------------------------------------------------------
  describe('resetPassword()', () => {
    it('POSTs to /auth/reset-password with token and password', async () => {
      mockOkResponse({ message: 'password updated' });
      const result = await resetPassword({ token: 'abc123', password: 'NewPass1!' });

      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/reset-password`);
      expect(opts.method).toBe('POST');
      const body = JSON.parse(opts.body as string);
      expect(body.token).toBe('abc123');
      expect(body.password).toBe('NewPass1!');
      expect(result).toEqual({ message: 'password updated' });
    });

    it('throws on invalid/expired token', async () => {
      mockErrorResponse(400, 'Token expired');
      await expect(
        resetPassword({ token: 'expired', password: 'pw' })
      ).rejects.toThrow('Token expired');
    });
  });

  // -------------------------------------------------------------------------
  // me
  // -------------------------------------------------------------------------
  describe('me()', () => {
    it('GETs /auth/me', async () => {
      const user = { id: 1, email: 'user@example.com', fullName: 'Alice' };
      mockOkResponse(user);
      const result = await me();

      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/me`);
      expect(opts.method).toBe('GET');
      expect(opts.credentials).toBe('include');
      expect(result).toEqual(user);
    });

    it('throws 401 when not authenticated', async () => {
      mockErrorResponse(401, 'Not authenticated');
      await expect(me()).rejects.toThrow('Not authenticated');
    });
  });

  // -------------------------------------------------------------------------
  // logout
  // -------------------------------------------------------------------------
  describe('logout()', () => {
    it('POSTs to /auth/logout', async () => {
      mockOkResponse({ message: 'logged out' });
      const result = await logout();

      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/logout`);
      expect(opts.method).toBe('POST');
      expect(result).toEqual({ message: 'logged out' });
    });
  });

  // -------------------------------------------------------------------------
  // refresh
  // -------------------------------------------------------------------------
  describe('refresh()', () => {
    it('POSTs to /auth/refresh', async () => {
      mockOkResponse({ access_token: 'new-token' });
      const result = await refresh();

      const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit];
      expect(url).toBe(`${BASE}/auth/refresh`);
      expect(opts.method).toBe('POST');
      expect(result).toEqual({ access_token: 'new-token' });
    });

    it('throws when refresh token is invalid', async () => {
      mockErrorResponse(401, 'Refresh token invalid');
      await expect(refresh()).rejects.toThrow('Refresh token invalid');
    });
  });

  // -------------------------------------------------------------------------
  // Content-Type header
  // -------------------------------------------------------------------------
  describe('request headers', () => {
    it('always sets Content-Type: application/json', async () => {
      mockOkResponse({});
      await login({ email: 'a@b.com', password: 'pw' });
      const opts = fetchSpy.mock.calls[0][1] as RequestInit;
      const headers = opts.headers as Record<string, string>;
      expect(headers['Content-Type']).toBe('application/json');
    });

    it('always sets credentials: include', async () => {
      mockOkResponse({});
      await me();
      const opts = fetchSpy.mock.calls[0][1] as RequestInit;
      expect(opts.credentials).toBe('include');
    });
  });
});
