import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from './AuthContext';
import * as authApi from '../api/auth';
import { getAccessToken, clearTokens } from './tokenStore';

// Mock the API module
jest.mock('../api/auth');

const mockedApiLogin = authApi.login as jest.MockedFunction<typeof authApi.login>;
const mockedApiRegister = authApi.register as jest.MockedFunction<typeof authApi.register>;
const mockedApiLogout = authApi.logout as jest.MockedFunction<typeof authApi.logout>;
const mockedApiMe = authApi.me as jest.MockedFunction<typeof authApi.me>;
const mockedApiRefresh = authApi.refresh as jest.MockedFunction<typeof authApi.refresh>;

// Also mock tokenStore so we can spy on it while still using real implementations
jest.mock('./tokenStore', () => ({
  getAccessToken: jest.fn(),
  setAccessToken: jest.fn(),
  clearTokens: jest.fn(),
}));

const mockedGetAccessToken = getAccessToken as jest.MockedFunction<typeof getAccessToken>;
const mockedClearTokens = clearTokens as jest.MockedFunction<typeof clearTokens>;

const rawUser = {
  id: 'user-1',
  full_name: 'John Doe',
  email: 'john@example.com',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
};

const mappedUser = {
  id: 'user-1',
  fullName: 'John Doe',
  email: 'john@example.com',
  isActive: true,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-02T00:00:00Z',
};

function TestConsumer() {
  const { user, isAuthenticated, isLoading, login, register, logout, refresh } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="user">{user ? user.fullName : 'none'}</span>
      <button onClick={() => login({ email: 'john@example.com', password: 'pass' })}>login</button>
      <button onClick={() => register({ email: 'jane@example.com', password: 'pass', full_name: 'Jane' })}>register</button>
      <button onClick={() => logout()}>logout</button>
      <button onClick={() => refresh()}>refresh</button>
    </div>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('AuthProvider', () => {
  describe('initial load — no token stored', () => {
    it('starts with isLoading=true then resolves to unauthenticated', async () => {
      mockedGetAccessToken.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      // After mount the effect runs synchronously enough that by the time
      // React flushes, isLoading becomes false without a token.
      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('none');
      expect(mockedApiMe).not.toHaveBeenCalled();
    });
  });

  describe('initial load — token exists, apiMe succeeds', () => {
    it('sets the user from apiMe response', async () => {
      mockedGetAccessToken.mockReturnValue('stored-token');
      mockedApiMe.mockResolvedValue(rawUser);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('John Doe');
    });
  });

  describe('initial load — token exists, apiMe fails, refresh succeeds', () => {
    it('calls refresh and sets user', async () => {
      mockedGetAccessToken.mockReturnValue('expired-token');
      // First call from useEffect fails
      mockedApiMe
        .mockRejectedValueOnce(new Error('401'))
        // Second call inside refresh succeeds
        .mockResolvedValueOnce(rawUser);
      mockedApiRefresh.mockResolvedValue({ access_token: 'new-token' });

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('John Doe');
      expect(mockedApiRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('initial load — token exists, apiMe fails, refresh also fails', () => {
    it('clears tokens and leaves user null', async () => {
      mockedGetAccessToken.mockReturnValue('bad-token');
      mockedApiMe.mockRejectedValue(new Error('401'));
      mockedApiRefresh.mockRejectedValue(new Error('refresh failed'));

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('none');
      expect(mockedClearTokens).toHaveBeenCalled();
    });
  });

  describe('login', () => {
    it('calls apiLogin, stores token, and sets user from apiMe', async () => {
      mockedGetAccessToken.mockReturnValue(null);
      mockedApiLogin.mockResolvedValue({ access_token: 'login-token' });
      mockedApiMe.mockResolvedValue(rawUser);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      await act(async () => {
        screen.getByText('login').click();
      });

      expect(mockedApiLogin).toHaveBeenCalledWith({ email: 'john@example.com', password: 'pass' });
      expect(mockedApiMe).toHaveBeenCalled();
      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('John Doe');
    });

    it('propagates error if apiLogin throws', async () => {
      mockedGetAccessToken.mockReturnValue(null);
      mockedApiLogin.mockRejectedValue(new Error('bad credentials'));

      let caughtError: Error | undefined;

      function ErrorConsumer() {
        const { login } = useAuth();
        return (
          <button
            onClick={async () => {
              try {
                await login({ email: 'x', password: 'y' });
              } catch (e) {
                caughtError = e as Error;
              }
            }}
          >
            login
          </button>
        );
      }

      render(
        <AuthProvider>
          <ErrorConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {});

      await act(async () => {
        screen.getByText('login').click();
      });

      expect(caughtError?.message).toBe('bad credentials');
    });
  });

  describe('register', () => {
    it('calls apiRegister, stores token, and sets user from apiMe', async () => {
      mockedGetAccessToken.mockReturnValue(null);
      mockedApiRegister.mockResolvedValue({ access_token: 'reg-token' });
      mockedApiMe.mockResolvedValue(rawUser);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      await act(async () => {
        screen.getByText('register').click();
      });

      expect(mockedApiRegister).toHaveBeenCalledWith({ email: 'jane@example.com', password: 'pass', full_name: 'Jane' });
      expect(mockedApiMe).toHaveBeenCalled();
      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('John Doe');
    });
  });

  describe('logout', () => {
    it('calls apiLogout, clears tokens, and sets user to null', async () => {
      mockedGetAccessToken.mockReturnValue('some-token');
      mockedApiMe.mockResolvedValue(rawUser);
      mockedApiLogout.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
      });

      await act(async () => {
        screen.getByText('logout').click();
      });

      expect(mockedApiLogout).toHaveBeenCalledTimes(1);
      expect(mockedClearTokens).toHaveBeenCalled();
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('none');
    });

    it('still clears tokens if apiLogout throws', async () => {
      mockedGetAccessToken.mockReturnValue('some-token');
      mockedApiMe.mockResolvedValue(rawUser);
      mockedApiLogout.mockRejectedValue(new Error('network'));

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
      });

      await act(async () => {
        screen.getByText('logout').click();
      });

      expect(mockedClearTokens).toHaveBeenCalled();
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
    });
  });

  describe('refresh', () => {
    it('calls apiRefresh and apiMe then sets user', async () => {
      mockedGetAccessToken.mockReturnValue(null);
      mockedApiRefresh.mockResolvedValue({ access_token: 'refreshed-token' });
      mockedApiMe.mockResolvedValue(rawUser);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      await act(async () => {
        screen.getByText('refresh').click();
      });

      expect(mockedApiRefresh).toHaveBeenCalledTimes(1);
      expect(mockedApiMe).toHaveBeenCalled();
      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user').textContent).toBe('John Doe');
    });

    it('clears tokens if apiRefresh throws', async () => {
      mockedGetAccessToken.mockReturnValue(null);
      mockedApiRefresh.mockRejectedValue(new Error('refresh error'));

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      await act(async () => {
        screen.getByText('refresh').click();
      });

      expect(mockedClearTokens).toHaveBeenCalled();
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user').textContent).toBe('none');
    });
  });
});

describe('useAuth outside AuthProvider', () => {
  it('throws an error', () => {
    function BareConsumer() {
      useAuth();
      return null;
    }

    // Suppress React's console.error for this expected throw
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<BareConsumer />)).toThrow('useAuth must be used within an AuthProvider');
    spy.mockRestore();
  });
});
