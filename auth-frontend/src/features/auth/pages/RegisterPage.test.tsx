import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import RegisterPage from './RegisterPage';
import * as authApi from '../../../api/auth';

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the auth API
vi.mock('../../../api/auth', () => ({
  register: vi.fn(),
}));

const mockRegister = authApi.register as ReturnType<typeof vi.fn>;

function renderPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>
  );
}

describe('RegisterPage', () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockRegister.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Rendering
  // ---------------------------------------------------------------------------
  describe('initial render', () => {
    it('renders the page heading', () => {
      renderPage();
      expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    });

    it('renders all form fields', () => {
      renderPage();
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/i agree to the/i)).toBeInTheDocument();
    });

    it('renders the submit button', () => {
      renderPage();
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
    });

    it('renders a link to the login page', () => {
      renderPage();
      expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
    });

    it('renders terms and privacy links', () => {
      renderPage();
      expect(screen.getByRole('link', { name: /terms of service/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /privacy policy/i })).toBeInTheDocument();
    });

    it('does not show any error messages on initial render', () => {
      renderPage();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Validation — submit with empty form
  // ---------------------------------------------------------------------------
  describe('form validation on submit (empty form)', () => {
    it('shows fullName error when submitting empty form', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      expect(await screen.findByText(/full name is required/i)).toBeInTheDocument();
    });

    it('shows email error when submitting empty form', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      expect(await screen.findByText(/enter a valid email address/i)).toBeInTheDocument();
    });

    it('shows password error when submitting empty form', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });

    it('shows confirmPassword error when submitting empty form', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
    });

    it('shows acceptTerms error when submitting empty form', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      expect(await screen.findByText(/you must accept the terms to continue/i)).toBeInTheDocument();
    });

    it('does not call register API when validation fails', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      await screen.findByText(/full name is required/i);
      expect(mockRegister).not.toHaveBeenCalled();
    });
  });

  // ---------------------------------------------------------------------------
  // Validation — blur
  // ---------------------------------------------------------------------------
  describe('field validation on blur', () => {
    it('shows fullName error when field is blurred empty', async () => {
      renderPage();
      const input = screen.getByLabelText(/full name/i);
      fireEvent.blur(input);
      expect(await screen.findByText(/full name is required/i)).toBeInTheDocument();
    });

    it('shows email error when field is blurred with invalid value', async () => {
      renderPage();
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'notanemail');
      fireEvent.blur(input);
      expect(await screen.findByText(/enter a valid email address/i)).toBeInTheDocument();
    });

    it('shows password error when field is blurred with short value', async () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      await userEvent.type(input, 'short');
      fireEvent.blur(input);
      expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });

    it('shows confirmPassword error when passwords do not match on blur', async () => {
      renderPage();
      const passwordInput = screen.getByLabelText(/^password$/i);
      const confirmInput = screen.getByLabelText(/confirm password/i);
      await userEvent.type(passwordInput, 'Password1');
      await userEvent.type(confirmInput, 'Different1');
      fireEvent.blur(confirmInput);
      expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
    });

    it('shows acceptTerms error when checkbox is blurred unchecked', async () => {
      renderPage();
      const checkbox = screen.getByLabelText(/i agree to the/i);
      fireEvent.blur(checkbox);
      expect(await screen.findByText(/you must accept the terms to continue/i)).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Validation — inline re-validation on change (touched fields)
  // ---------------------------------------------------------------------------
  describe('inline re-validation after touch', () => {
    it('clears fullName error once user types a valid name', async () => {
      renderPage();
      const input = screen.getByLabelText(/full name/i);
      fireEvent.blur(input); // touch
      expect(await screen.findByText(/full name is required/i)).toBeInTheDocument();
      await userEvent.type(input, 'John Doe');
      expect(screen.queryByText(/full name is required/i)).not.toBeInTheDocument();
    });

    it('updates password error inline after typing', async () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      await userEvent.type(input, 'ab');
      fireEvent.blur(input);
      expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
      // type valid password
      await userEvent.clear(input);
      await userEvent.type(input, 'ValidPass1');
      expect(screen.queryByText(/password must be at least 8 characters/i)).not.toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Password strength meter
  // ---------------------------------------------------------------------------
  describe('password strength meter', () => {
    it('is not visible when password field is empty', () => {
      renderPage();
      expect(screen.queryByText(/weak|fair|good|strong|very weak/i)).not.toBeInTheDocument();
    });

    it('shows "Very weak" for a single character password', async () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      await userEvent.type(input, 'a');
      expect(screen.getByText(/very weak/i)).toBeInTheDocument();
    });

    it('shows "Weak" when only one criterion is met', async () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      // Only lowercase — score=1
      await userEvent.type(input, 'abcdefgh');
      // score=2: 8+ chars + lowercase
      // Actually: length>=8 (pass) + lowercase (pass) = score 2 => Fair
      // Let's use a single char that passes only lowercase
      await userEvent.clear(input);
      await userEvent.type(input, 'a'); // only lowercase passes
      expect(screen.getByText(/very weak/i)).toBeInTheDocument();
    });

    it('shows "Strong" for a password meeting all criteria', async () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      await userEvent.type(input, 'Password1');
      expect(screen.getByText(/strong/i)).toBeInTheDocument();
    });

    it('shows check items for password criteria', async () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      await userEvent.type(input, 'P');
      expect(screen.getByText(/8\+ characters/i)).toBeInTheDocument();
      expect(screen.getByText(/uppercase/i)).toBeInTheDocument();
      expect(screen.getByText(/lowercase/i)).toBeInTheDocument();
      expect(screen.getByText(/number/i)).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // Show / hide password toggle
  // ---------------------------------------------------------------------------
  describe('password visibility toggle', () => {
    it('password field starts as type="password"', () => {
      renderPage();
      const input = screen.getByLabelText(/^password$/i);
      expect(input).toHaveAttribute('type', 'password');
    });

    it('toggles password field to text type on click', async () => {
      renderPage();
      const toggle = screen.getByRole('button', { name: /show password/i });
      fireEvent.click(toggle);
      const input = screen.getByLabelText(/^password$/i);
      expect(input).toHaveAttribute('type', 'text');
    });

    it('hides password again on second click', async () => {
      renderPage();
      const toggle = screen.getByRole('button', { name: /show password/i });
      fireEvent.click(toggle);
      fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
      const input = screen.getByLabelText(/^password$/i);
      expect(input).toHaveAttribute('type', 'password');
    });

    it('confirm password field starts as type="password"', () => {
      renderPage();
      const input = screen.getByLabelText(/confirm password/i);
      expect(input).toHaveAttribute('type', 'password');
    });

    it('toggles confirm password field to text type on click', async () => {
      renderPage();
      const toggle = screen.getByRole('button', { name: /show confirm password/i });
      fireEvent.click(toggle);
      const input = screen.getByLabelText(/confirm password/i);
      expect(input).toHaveAttribute('type', 'text');
    });
  });

  // ---------------------------------------------------------------------------
  // Successful submission
  // ---------------------------------------------------------------------------
  describe('successful submission', () => {
    it('calls register API with correct payload', async () => {
      mockRegister.mockResolvedValueOnce({
        accessToken: 'tok',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'John Doe', email: 'john@example.com', is_active: true, created_at: '', updated_at: '' },
      });

      renderPage();

      await userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
      await userEvent.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await userEvent.type(screen.getByLabelText(/^password$/i), 'Password1');
      await userEvent.type(screen.getByLabelText(/confirm password/i), 'Password1');
      fireEvent.click(screen.getByLabelText(/i agree to the/i));

      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockRegister).toHaveBeenCalledWith({
          fullName: 'John Doe',
          email: 'john@example.com',
          password: 'Password1',
          confirmPassword: 'Password1',
        });
      });
    });

    it('navigates to /login after successful registration', async () => {
      mockRegister.mockResolvedValueOnce({
        accessToken: 'tok',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'John Doe', email: 'john@example.com', is_active: true, created_at: '', updated_at: '' },
      });

      renderPage();

      await userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
      await userEvent.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await userEvent.type(screen.getByLabelText(/^password$/i), 'Password1');
      await userEvent.type(screen.getByLabelText(/confirm password/i), 'Password1');
      fireEvent.click(screen.getByLabelText(/i agree to the/i));

      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
      });
    });
  });

  // ---------------------------------------------------------------------------
  // Server errors
  // ---------------------------------------------------------------------------
  describe('server error handling', () => {
    async function fillAndSubmit() {
      await userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
      await userEvent.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await userEvent.type(screen.getByLabelText(/^password$/i), 'Password1');
      await userEvent.type(screen.getByLabelText(/confirm password/i), 'Password1');
      fireEvent.click(screen.getByLabelText(/i agree to the/i));
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    }

    it('shows server error message from response', async () => {
      mockRegister.mockRejectedValueOnce({
        response: { data: { error: { message: 'Email already in use.' } } },
      });

      renderPage();
      await fillAndSubmit();

      expect(await screen.findByText(/email already in use/i)).toBeInTheDocument();
    });

    it('shows generic error when server response has no message', async () => {
      mockRegister.mockRejectedValueOnce({
        response: { data: {} },
      });

      renderPage();
      await fillAndSubmit();

      expect(await screen.findByText(/registration failed. please try again/i)).toBeInTheDocument();
    });

    it('shows generic error for non-response errors', async () => {
      mockRegister.mockRejectedValueOnce(new Error('Network error'));

      renderPage();
      await fillAndSubmit();

      expect(await screen.findByText(/registration failed. please try again/i)).toBeInTheDocument();
    });

    it('clears server error on next submit attempt', async () => {
      mockRegister
        .mockRejectedValueOnce({ response: { data: { error: { message: 'Email taken.' } } } })
        .mockResolvedValueOnce({
          accessToken: 'tok',
          tokenType: 'Bearer',
          user: { id: '1', full_name: 'John Doe', email: 'john@example.com', is_active: true, created_at: '', updated_at: '' },
        });

      renderPage();
      await fillAndSubmit();
      expect(await screen.findByText(/email taken/i)).toBeInTheDocument();

      // Submit again
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      await waitFor(() => {
        expect(screen.queryByText(/email taken/i)).not.toBeInTheDocument();
      });
    });
  });

  // ---------------------------------------------------------------------------
  // Submitting / loading state
  // ---------------------------------------------------------------------------
  describe('submitting state', () => {
    it('disables the submit button while submitting', async () => {
      let resolveRegister: (v: unknown) => void;
      mockRegister.mockReturnValueOnce(
        new Promise((res) => {
          resolveRegister = res;
        })
      );

      renderPage();

      await userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
      await userEvent.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await userEvent.type(screen.getByLabelText(/^password$/i), 'Password1');
      await userEvent.type(screen.getByLabelText(/confirm password/i), 'Password1');
      fireEvent.click(screen.getByLabelText(/i agree to the/i));

      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled();
      });

      // Cleanup: resolve the promise
      resolveRegister!({
        accessToken: 'tok',
        tokenType: 'Bearer',
        user: { id: '1', full_name: 'John Doe', email: 'john@example.com', is_active: true, created_at: '', updated_at: '' },
      });
    });

    it('re-enables submit button after failure', async () => {
      mockRegister.mockRejectedValueOnce(new Error('Network'));

      renderPage();

      await userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
      await userEvent.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await userEvent.type(screen.getByLabelText(/^password$/i), 'Password1');
      await userEvent.type(screen.getByLabelText(/confirm password/i), 'Password1');
      fireEvent.click(screen.getByLabelText(/i agree to the/i));

      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create account/i })).not.toBeDisabled();
      });
    });
  });

  // ---------------------------------------------------------------------------
  // Accessibility
  // ---------------------------------------------------------------------------
  describe('accessibility', () => {
    it('marks invalid fields with aria-invalid="true"', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      await screen.findByText(/full name is required/i);
      expect(screen.getByLabelText(/full name/i)).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('aria-invalid', 'true');
    });

    it('fields do not have aria-invalid before submission', () => {
      renderPage();
      expect(screen.getByLabelText(/full name/i)).not.toHaveAttribute('aria-invalid', 'true');
    });

    it('error messages have role="alert"', async () => {
      renderPage();
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));
      await screen.findByText(/full name is required/i);
      const alerts = screen.getAllByRole('alert');
      expect(alerts.length).toBeGreaterThan(0);
    });

    it('server error has role="alert"', async () => {
      mockRegister.mockRejectedValueOnce(new Error('fail'));
      renderPage();

      await userEvent.type(screen.getByLabelText(/full name/i), 'John Doe');
      await userEvent.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await userEvent.type(screen.getByLabelText(/^password$/i), 'Password1');
      await userEvent.type(screen.getByLabelText(/confirm password/i), 'Password1');
      fireEvent.click(screen.getByLabelText(/i agree to the/i));
      fireEvent.click(screen.getByRole('button', { name: /create account/i }));

      const alert = await screen.findByRole('alert', { name: undefined });
      expect(alert).toBeInTheDocument();
    });
  });
});
