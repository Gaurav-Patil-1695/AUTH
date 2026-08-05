import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

// Auth context / hooks
vi.mock('./features/auth/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Guard components — render the Outlet so nested routes are visible
vi.mock('./features/auth/RequireAuth', () => ({
  default: () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { Outlet } = require('react-router-dom');
    return <Outlet />;
  },
}));

vi.mock('./features/auth/RequireGuest', () => ({
  default: () => {
    const { Outlet } = require('react-router-dom');
    return <Outlet />;
  },
}));

// Page stubs
vi.mock('./features/auth/pages/LoginPage', () => ({
  default: () => <div data-testid="login-page">LoginPage</div>,
}));

vi.mock('./features/auth/pages/RegisterPage', () => ({
  default: () => <div data-testid="register-page">RegisterPage</div>,
}));

vi.mock('./features/auth/pages/ForgotPasswordPage', () => ({
  default: () => <div data-testid="forgot-password-page">ForgotPasswordPage</div>,
}));

vi.mock('./features/auth/pages/ResetPasswordPage', () => ({
  default: () => <div data-testid="reset-password-page">ResetPasswordPage</div>,
}));

vi.mock('./pages/ProfilePage', () => ({
  default: () => <div data-testid="profile-page">ProfilePage</div>,
}));

vi.mock('./features/auth/LogoutRoute', () => ({
  default: () => <div data-testid="logout-route">LogoutRoute</div>,
}));

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('App routing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders LoginPage at /login', () => {
    renderAt('/login');
    expect(screen.getByTestId('login-page')).toBeTruthy();
  });

  it('renders RegisterPage at /register', () => {
    renderAt('/register');
    expect(screen.getByTestId('register-page')).toBeTruthy();
  });

  it('renders ForgotPasswordPage at /forgot-password', () => {
    renderAt('/forgot-password');
    expect(screen.getByTestId('forgot-password-page')).toBeTruthy();
  });

  it('renders ResetPasswordPage at /reset-password', () => {
    renderAt('/reset-password');
    expect(screen.getByTestId('reset-password-page')).toBeTruthy();
  });

  it('renders ProfilePage at /profile (behind RequireAuth)', () => {
    renderAt('/profile');
    expect(screen.getByTestId('profile-page')).toBeTruthy();
  });

  it('renders LogoutRoute at /logout', () => {
    renderAt('/logout');
    expect(screen.getByTestId('logout-route')).toBeTruthy();
  });

  it('redirects unknown paths to /login', () => {
    renderAt('/some/unknown/path');
    // After redirect the login page stub should be rendered
    expect(screen.getByTestId('login-page')).toBeTruthy();
  });

  it('redirects root path / to /login', () => {
    renderAt('/');
    expect(screen.getByTestId('login-page')).toBeTruthy();
  });
});
