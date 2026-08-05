import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProfilePage from './ProfilePage';
import { AuthContext } from '../features/auth/context/AuthContext';
import * as authApi from '../api/auth';

// Mock react-router-dom's useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock the auth API
jest.mock('../api/auth', () => ({
  logout: jest.fn(),
}));

const mockLogout = authApi.logout as jest.MockedFunction<typeof authApi.logout>;

const baseUser: authApi.UserResponse = {
  id: '1',
  full_name: 'Jane Doe',
  email: 'jane@example.com',
  is_active: true,
  created_at: '2023-06-15T00:00:00Z',
  updated_at: '2023-06-15T00:00:00Z',
};

function buildContext(overrides: Partial<{
  isLoading: boolean;
  isAuthenticated: boolean;
  user: authApi.UserResponse | null;
  logout: () => void;
}> = {}) {
  return {
    isLoading: false,
    isAuthenticated: true,
    user: baseUser,
    logout: jest.fn(),
    ...overrides,
  };
}

function renderWithContext(contextValue: ReturnType<typeof buildContext> | null) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={contextValue as any}>
        <ProfilePage />
      </AuthContext.Provider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('ProfilePage – loading state', () => {
  it('shows loading indicator when authContext is loading', () => {
    renderWithContext(buildContext({ isLoading: true, user: null }));
    expect(screen.getByRole('status')).toHaveTextContent('Loading profile');
  });

  it('shows loading indicator when authContext is null', () => {
    renderWithContext(null);
    expect(screen.getByRole('status')).toHaveTextContent('Loading profile');
  });
});

describe('ProfilePage – redirect when not authenticated', () => {
  it('navigates to /login when not authenticated and not loading', () => {
    renderWithContext(buildContext({ isAuthenticated: false, user: null }));
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('does NOT navigate when authenticated', () => {
    renderWithContext(buildContext());
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

describe('ProfilePage – renders null when user is missing', () => {
  it('renders nothing if isAuthenticated but user is null (no redirect race)', () => {
    // isAuthenticated=true but user is null – the component returns null
    const ctx = buildContext({ isAuthenticated: true, user: null });
    const { container } = renderWithContext(ctx);
    // Only the <style> tag or truly empty – no main content
    // The component returns null in this branch
    expect(container.querySelector('main')).toBeNull();
  });
});

describe('ProfilePage – profile content', () => {
  it('renders the branding title', () => {
    renderWithContext(buildContext());
    expect(screen.getByText('auth-starter')).toBeInTheDocument();
  });

  it('renders the correct avatar initials for a two-part name', () => {
    renderWithContext(buildContext());
    // Jane Doe → JD
    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('renders a single-part name initial correctly', () => {
    renderWithContext(buildContext({ user: { ...baseUser, full_name: 'Madonna' } }));
    expect(screen.getByText('M')).toBeInTheDocument();
  });

  it('renders the user full name', () => {
    renderWithContext(buildContext());
    expect(screen.getByText('Jane Doe')).toBeInTheDocument();
  });

  it('renders the user email', () => {
    renderWithContext(buildContext());
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
  });

  it('renders Active badge when user is active', () => {
    renderWithContext(buildContext());
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders Inactive badge when user is inactive', () => {
    renderWithContext(buildContext({ user: { ...baseUser, is_active: false } }));
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('renders the member since date', () => {
    renderWithContext(buildContext());
    // 2023-06-15 → "June 15, 2023" in en-US locale
    expect(screen.getByText(/june 15, 2023/i)).toBeInTheDocument();
  });

  it('does not render Member Since field when createdAt is empty', () => {
    renderWithContext(buildContext({ user: { ...baseUser, created_at: '' } }));
    expect(screen.queryByText('Member Since')).toBeNull();
  });

  it('renders the Sign Out button', () => {
    renderWithContext(buildContext());
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
  });

  it('uses camelCase properties (fullName, isActive, createdAt) when present', () => {
    const camelUser: authApi.UserResponse = {
      ...baseUser,
      full_name: '',
      fullName: 'Alice Smith',
      is_active: false,
      isActive: true,
      created_at: '',
      createdAt: '2022-01-01T00:00:00Z',
    };
    renderWithContext(buildContext({ user: camelUser }));
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText(/january 1, 2022/i)).toBeInTheDocument();
  });
});

describe('ProfilePage – logout', () => {
  it('calls logout API and context logout, then navigates to /login on success', async () => {
    const contextLogout = jest.fn();
    mockLogout.mockResolvedValueOnce(undefined);
    const ctx = buildContext({ logout: contextLogout });
    renderWithContext(ctx);

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledTimes(1);
      expect(contextLogout).toHaveBeenCalledTimes(1);
      expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
    });
  });

  it('shows spinner and disables button while logging out', async () => {
    // Keep the promise pending so we can inspect mid-flight state
    let resolve!: () => void;
    mockLogout.mockReturnValueOnce(new Promise<void>(r => { resolve = r; }));
    renderWithContext(buildContext());

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));

    // Button should be disabled mid-flight
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText(/signing out/i)).toBeInTheDocument();

    resolve();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalled());
  });

  it('shows error banner and re-enables button when logout API throws', async () => {
    mockLogout.mockRejectedValueOnce(new Error('Network error'));
    renderWithContext(buildContext());

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        'An unexpected error occurred. Please try again.'
      );
    });

    // Button should be re-enabled
    expect(screen.getByRole('button', { name: /sign out/i })).not.toBeDisabled();
  });

  it('clears error banner on subsequent logout attempt', async () => {
    // First call fails, second succeeds
    mockLogout
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce(undefined);
    const contextLogout = jest.fn();
    renderWithContext(buildContext({ logout: contextLogout }));

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));
    // Error should clear immediately (setLogoutError(null) called)
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
  });
});

describe('getInitials (via avatar rendering)', () => {
  it('returns ? for an empty name', () => {
    renderWithContext(buildContext({ user: { ...baseUser, full_name: '' } }));
    expect(screen.getByText('?')).toBeInTheDocument();
  });

  it('handles whitespace-only name as empty', () => {
    renderWithContext(buildContext({ user: { ...baseUser, full_name: '   ' } }));
    expect(screen.getByText('?')).toBeInTheDocument();
  });

  it('uses first and last initial for multi-word names', () => {
    renderWithContext(buildContext({ user: { ...baseUser, full_name: 'John Michael Doe' } }));
    // first=J, last=D
    expect(screen.getByText('JD')).toBeInTheDocument();
  });
});
