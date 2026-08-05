import { ApiError } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

function drainQueue(token: string | null): void {
  refreshQueue.forEach((resolve) => resolve(token));
  refreshQueue = [];
}

async function attemptSilentRefresh(): Promise<string | null> {
  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      return null;
    }
    const data = await response.json();
    const token: string | null = data?.access_token ?? null;
    if (token) {
      localStorage.setItem('access_token', token);
    }
    return token;
  } catch {
    return null;
  }
}

function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const buildHeaders = (token: string | null): HeadersInit => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(init.headers as Record<string, string> | undefined),
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  const doFetch = (token: string | null): Promise<Response> =>
    fetch(url, {
      ...init,
      credentials: 'include',
      headers: buildHeaders(token),
    });

  let response = await doFetch(getAccessToken());

  if (response.status === 401) {
    if (isRefreshing) {
      const newToken = await new Promise<string | null>((resolve) => {
        refreshQueue.push(resolve);
      });
      if (!newToken) {
        throw buildApiError(response, {
          error: {
            code: 'UNAUTHORIZED',
            message: 'Session expired. Please log in again.',
            details: {},
          },
        });
      }
      response = await doFetch(newToken);
    } else {
      isRefreshing = true;
      const newToken = await attemptSilentRefresh();
      isRefreshing = false;
      drainQueue(newToken);

      if (!newToken) {
        localStorage.removeItem('access_token');
        throw buildApiError(response, {
          error: {
            code: 'UNAUTHORIZED',
            message: 'Session expired. Please log in again.',
            details: {},
          },
        });
      }
      response = await doFetch(newToken);
    }
  }

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    throw buildApiError(response, body);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

function buildApiError(response: Response, body: unknown): ApiError {
  const fallback = {
    code: 'UNKNOWN_ERROR',
    message: `Request failed with status ${response.status}`,
    details: {} as Record<string, string[]>,
  };

  if (
    body !== null &&
    typeof body === 'object' &&
    'error' in (body as object)
  ) {
    const err = (body as { error: unknown }).error;
    if (err !== null && typeof err === 'object') {
      const e = err as Record<string, unknown>;
      return new ApiError(
        response.status,
        typeof e['code'] === 'string' ? e['code'] : fallback.code,
        typeof e['message'] === 'string' ? e['message'] : fallback.message,
        (e['details'] as Record<string, string[]> | undefined) ?? {},
      );
    }
  }

  return new ApiError(
    response.status,
    fallback.code,
    fallback.message,
    fallback.details,
  );
}
