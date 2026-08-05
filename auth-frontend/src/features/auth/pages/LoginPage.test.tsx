import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LoginPage from './LoginPage';
import * as authApi from '../../../api/auth';

// Mock the auth API module
vi.mock('../../../api/auth', () => ({
  login: vi.fn(),
}));

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('renders the sign in heading', () => {
      renderLoginPage();
      expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    });

    it('renders the email input', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });

    it('renders the password input', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    });

    it('renders the remember me checkbox', () => {
      renderLoginPage();
      expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
    });

    it('renders the forgot password link', () => {
      renderLoginPage();
      expect(screen.getByRole('link', { name: /forgot password/i })).toBeInTheDocument();
    });

    it('renders the create account link', () => {
      renderLoginPage();
      expect(screen.getByRole('link', { name: /create account/i })).toBeInTheDocument();
    });

    it('renders the submit button', () => {
      renderLoginPage();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('renders the brand name', () => {
      renderLoginPage();
      expect(screen.getByText('auth-starter')).toBeInTheDocument();
    });

    it('password input is of type password by default', () => {
      renderLoginPage();
      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('does not show form error initially', () => {
      renderLoginPage();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Form validation', () => {
    it('shows email error when email is empty on submit', async () => {
      renderLoginPage();
      fireEvent.submit(screen.getByRole('form') ?? screen.getByRole('form', { hidden: true }) ?? document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
      });
    });

    it('shows password error when password is empty on submit', async () => {
      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Password is required.')).toBeInTheDocument();
      });
    });

    it('shows email error for invalid email format', async () => {
      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      fireEvent.change(emailInput, { target: { value: 'notanemail' } });
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
      });
    });

    it('shows both email and password errors when both are empty', async () => {
      renderLoginPage();
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
        expect(screen.getByText('Password is required.')).toBeInTheDocument();
      });
    });

    it('clears email error when user starts typing in email field', async () => {
      renderLoginPage();
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
      });
      const emailInput = screen.getByLabelText(/email address/i);
      fireEvent.change(emailInput, { target: { value: 'a' } });
      await waitFor(() => {
        expect(screen.queryByText('Enter a valid email address.')).not.toBeInTheDocument();
      });
    });

    it('clears password error when user starts typing in password field', async () => {
      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Password is required.')).toBeInTheDocument();
      });
      const passwordInput = screen.getByLabelText(/^password$/i);
      fireEvent.change(passwordInput, { target: { value: 'p' } });
      await waitFor(() => {
        expect(screen.queryByText('Password is required.')).not.toBeInTheDocument();
      });
    });

    it('does not call login API when validation fails', async () => {
      renderLoginPage();
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
      });
      expect(authApi.login).not.toHaveBeenCalled();
    });

    it('sets aria-invalid on email input when there is an email error', async () => {
      renderLoginPage();
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('sets aria-invalid on password input when there is a password error', async () => {
      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.submit(document.querySelector('form')!);
      await waitFor(() => {
        expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('aria-invalid', 'true');
      });
    });
  });

  describe('Password visibility toggle', () => {
    it('toggles password visibility when show password button is clicked', async () => {
      renderLoginPage();
      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');

      const toggleButton = screen.getByRole('button', { name: /show password/i });
      fireEvent.click(toggleButton);

      expect(passwordInput).toHaveAttribute('type', 'text');
    });

    it('toggles password back to hidden after second click', async () => {
      renderLoginPage();
      const passwordInput = screen.getByLabelText(/^password$/i);
      const toggleButton = screen.getByRole('button', { name: /show password/i });

      fireEvent.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');

      const hideButton = screen.getByRole('button', { name: /hide password/i });
      fireEvent.click(hideButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('shows "Hide password" label when password is visible', () => {
      renderLoginPage();
      const toggleButton = screen.getByRole('button', { name: /show password/i });
      fireEvent.click(toggleButton);
      expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();
    });
  });

  describe('Remember me checkbox', () => {
    it('is unchecked by default', () => {
      renderLoginPage();
      const checkbox = screen.getByLabelText(/remember me/i);
      expect(checkbox).not.toBeChecked();
    });

    it('can be checked', () => {
      renderLoginPage();
      const checkbox = screen.getByLabelText(/remember me/i);
      fireEvent.click(checkbox);
      expect(checkbox).toBeChecked();
    });

    it('can be unchecked after being checked', () => {
      renderLoginPage();
      const checkbox = screen.getByLabelText(/remember me/i);
      fireEvent.click(checkbox);
      fireEvent.click(checkbox);
      expect(checkbox).not.toBeChecked();
    });
  });

  describe('Successful login', () => {
    it('calls login API with correct payload', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockResolvedValueOnce({
        accessToken: 'token123',
        tokenType: 'Bearer',
        user: {
          id: '1',
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      });

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          rememberMe: false,
        });
      });
    });

    it('navigates to / after successful login', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockResolvedValueOnce({
        accessToken: 'token123',
        tokenType: 'Bearer',
        user: {
          id: '1',
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      });

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('passes rememberMe=true when checkbox is checked', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockResolvedValueOnce({
        accessToken: 'token123',
        tokenType: 'Bearer',
        user: {
          id: '1',
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      });

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const rememberMe = screen.getByLabelText(/remember me/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(rememberMe);
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          rememberMe: true,
        });
      });
    });

    it('trims whitespace from email before submitting', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockResolvedValueOnce({
        accessToken: 'token123',
        tokenType: 'Bearer',
        user: {
          id: '1',
          full_name: 'Test User',
          email: 'test@example.com',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      });

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: '  test@example.com  ' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          rememberMe: false,
        });
      });
    });
  });

  describe('Failed login', () => {
    it('shows form error when login API throws an Error', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Invalid credentials');
      });
    });

    it('shows generic error message when login throws a non-Error', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockRejectedValueOnce({ error: { code: 'UNAUTHORIZED', message: 'Unauthorized' } });

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Invalid email or password.');
      });
    });

    it('does not navigate on failed login', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Submitting state', () => {
    it('disables the submit button while submitting', async () => {
      const mockLogin = vi.mocked(authApi.login);
      let resolveLogin!: (value: any) => void;
      mockLogin.mockImplementationOnce(
        () => new Promise((resolve) => { resolveLogin = resolve; })
      );

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();
      });

      resolveLogin({
        accessToken: 'token',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'Test', email: 'test@example.com', is_active: true, created_at: '', updated_at: '' },
      });
    });

    it('disables email input while submitting', async () => {
      const mockLogin = vi.mocked(authApi.login);
      let resolveLogin!: (value: any) => void;
      mockLogin.mockImplementationOnce(
        () => new Promise((resolve) => { resolveLogin = resolve; })
      );

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByLabelText(/email address/i)).toBeDisabled();
      });

      resolveLogin({
        accessToken: 'token',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'Test', email: 'test@example.com', is_active: true, created_at: '', updated_at: '' },
      });
    });

    it('disables password input while submitting', async () => {
      const mockLogin = vi.mocked(authApi.login);
      let resolveLogin!: (value: any) => void;
      mockLogin.mockImplementationOnce(
        () => new Promise((resolve) => { resolveLogin = resolve; })
      );

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByLabelText(/^password$/i)).toBeDisabled();
      });

      resolveLogin({
        accessToken: 'token',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'Test', email: 'test@example.com', is_active: true, created_at: '', updated_at: '' },
      });
    });

    it('shows "Signing in…" button text while submitting', async () => {
      const mockLogin = vi.mocked(authApi.login);
      let resolveLogin!: (value: any) => void;
      mockLogin.mockImplementationOnce(
        () => new Promise((resolve) => { resolveLogin = resolve; })
      );

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByText(/signing in/i)).toBeInTheDocument();
      });

      resolveLogin({
        accessToken: 'token',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'Test', email: 'test@example.com', is_active: true, created_at: '', updated_at: '' },
      });
    });

    it('re-enables inputs after login resolves', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockResolvedValueOnce({
        accessToken: 'token',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'Test', email: 'test@example.com', is_active: true, created_at: '', updated_at: '' },
      });

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('re-enables inputs after login rejects', async () => {
      const mockLogin = vi.mocked(authApi.login);
      mockLogin.mockRejectedValueOnce(new Error('Server error'));

      renderLoginPage();
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.submit(document.querySelector('form')!);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/email address/i)).not.toBeDisabled();
      expect(screen.getByLabelText(/^password$/i)).not.toBeDisabled();
    });
  });

  describe('Navigation links', () => {
    it('forgot password link points to /forgot-password', () => {
      renderLoginPage();
      const link = screen.getByRole('link', { name: /forgot password/i });
      expect(link).toHaveAttribute('href', '/forgot-password');
    });

    it('create account link points to /register', () => {
      renderLoginPage();
      const link = screen.getByRole('link', { name: /create account/i });
      expect(link).toHaveAttribute('href', '/register');
    });
  });
});
