import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Route guard logic tests.
// RequireAuth redirects unauthenticated users to /login.
// RequireGuest redirects authenticated users to /profile.
//
// We test the pure decision logic (should redirect / should render children)
// without rendering React components.
// ---------------------------------------------------------------------------

type AuthState = {
  isAuthenticated: boolean;
  isLoading: boolean;
};

/**
 * Returns the redirect path for RequireAuth, or null if the user may proceed.
 */
function requireAuthDecision(
  auth: AuthState,
  redirectTo = '/login'
): string | null {
  if (auth.isLoading) return null; // still loading — don't redirect yet
  if (!auth.isAuthenticated) return redirectTo;
  return null;
}

/**
 * Returns the redirect path for RequireGuest, or null if the user may proceed.
 */
function requireGuestDecision(
  auth: AuthState,
  redirectTo = '/profile'
): string | null {
  if (auth.isLoading) return null;
  if (auth.isAuthenticated) return redirectTo;
  return null;
}

describe('requireAuthDecision (RequireAuth logic)', () => {
  it('returns null (allow) when authenticated', () => {
    expect(requireAuthDecision({ isAuthenticated: true, isLoading: false })).toBeNull();
  });

  it('returns /login when not authenticated', () => {
    expect(requireAuthDecision({ isAuthenticated: false, isLoading: false })).toBe('/login');
  });

  it('returns null while loading (avoid premature redirect)', () => {
    expect(requireAuthDecision({ isAuthenticated: false, isLoading: true })).toBeNull();
  });

  it('returns null while loading even if already authenticated', () => {
    expect(requireAuthDecision({ isAuthenticated: true, isLoading: true })).toBeNull();
  });

  it('honours a custom redirect path', () => {
    expect(
      requireAuthDecision({ isAuthenticated: false, isLoading: false }, '/sign-in')
    ).toBe('/sign-in');
  });
});

describe('requireGuestDecision (RequireGuest logic)', () => {
  it('returns null (allow) when not authenticated', () => {
    expect(requireGuestDecision({ isAuthenticated: false, isLoading: false })).toBeNull();
  });

  it('returns /profile when authenticated', () => {
    expect(requireGuestDecision({ isAuthenticated: true, isLoading: false })).toBe('/profile');
  });

  it('returns null while loading', () => {
    expect(requireGuestDecision({ isAuthenticated: false, isLoading: true })).toBeNull();
  });

  it('returns null while loading even if authenticated', () => {
    expect(requireGuestDecision({ isAuthenticated: true, isLoading: true })).toBeNull();
  });

  it('honours a custom redirect path', () => {
    expect(
      requireGuestDecision({ isAuthenticated: true, isLoading: false }, '/dashboard')
    ).toBe('/dashboard');
  });
});
