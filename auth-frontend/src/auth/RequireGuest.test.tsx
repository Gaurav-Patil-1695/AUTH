import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RequireGuest } from './RequireGuest';
import { useAuth } from './AuthContext';

jest.mock('./AuthContext');

const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

function renderWithRouter(ui: React.ReactElement, initialPath = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={ui} />
        <Route path="/profile" element={<div data-testid="profile-page">Profile</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RequireGuest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders null while loading', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    const { container } = renderWithRouter(
      <RequireGuest>
        <div data-testid="guest-content">Guest Only</div>
      </RequireGuest>,
    );

    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId('guest-content')).toBeNull();
  });

  it('renders children when not authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    renderWithRouter(
      <RequireGuest>
        <div data-testid="guest-content">Guest Only</div>
      </RequireGuest>,
    );

    expect(screen.getByTestId('guest-content')).toBeInTheDocument();
    expect(screen.queryByTestId('profile-page')).toBeNull();
  });

  it('redirects to /profile when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: {
        id: '1',
        fullName: 'Alice',
        email: 'alice@example.com',
        isActive: true,
        createdAt: '',
        updatedAt: '',
      },
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    renderWithRouter(
      <RequireGuest>
        <div data-testid="guest-content">Guest Only</div>
      </RequireGuest>,
    );

    expect(screen.getByTestId('profile-page')).toBeInTheDocument();
    expect(screen.queryByTestId('guest-content')).toBeNull();
  });
});
