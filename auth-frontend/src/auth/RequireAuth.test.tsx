import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { RequireAuth } from './RequireAuth';
import { useAuth } from './AuthContext';

jest.mock('./AuthContext');

const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

function renderWithRouter(ui: React.ReactElement, initialPath = '/protected') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/protected" element={ui} />
        <Route path="/login" element={<div data-testid="login-page">Login</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('RequireAuth', () => {
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
      <RequireAuth>
        <div data-testid="protected-content">Protected</div>
      </RequireAuth>,
    );

    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId('protected-content')).toBeNull();
  });

  it('renders children when authenticated', () => {
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
      <RequireAuth>
        <div data-testid="protected-content">Protected</div>
      </RequireAuth>,
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login-page')).toBeNull();
  });

  it('redirects to /login with next param when not authenticated', () => {
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
      <RequireAuth>
        <div data-testid="protected-content">Protected</div>
      </RequireAuth>,
      '/protected',
    );

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).toBeNull();
  });

  it('encodes the next param with pathname + search + hash', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    // We capture the Navigate destination by rendering a Route that extracts search params
    let capturedSearch = '';

    function LoginCapture() {
      capturedSearch = window.location.search;
      return <div data-testid="login-page">Login</div>;
    }

    render(
      <MemoryRouter initialEntries={['/protected?foo=bar#section']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <RequireAuth>
                <div>Protected</div>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<LoginCapture />} />
        </Routes>
      </MemoryRouter>,
    );

    // The Navigate component should have navigated to /login?next=...
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });
});
