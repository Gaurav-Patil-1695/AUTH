import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ResetPasswordPage from './ResetPasswordPage';
import * as authApi from '../../../api/auth';

// Mock the auth API module
jest.mock('../../../api/auth', () => ({
  resetPassword: jest.fn(),
}));

const mockedResetPassword = authApi.resetPassword as jest.MockedFunction<typeof authApi.resetPassword>;

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Helper to render with router
function renderPage(search = '?token=valid-token') {
  return render(
    <MemoryRouter initialEntries={[`/reset-password${search}`]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('ResetPasswordPage rendering', () => {
  test('renders the page title and subtitle', () => {
    renderPage();
    expect(screen.getByText('Set new password')).toBeInTheDocument();
    expect(screen.getByText(/Choose a strong password/i)).toBeInTheDocument();
  });

  test('renders New Password and Confirm Password fields', () => {
    renderPage();
    expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
  });

  test('renders the submit button with correct label', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /Reset Password/i })).toBeInTheDocument();
  });

  test('renders the back to sign in link', () => {
    renderPage();
    expect(screen.getByRole('link', { name: /Back to Sign in/i })).toBeInTheDocument();
  });

  test('renders brand name', () => {
    renderPage();
    expect(screen.getByText('auth-starter')).toBeInTheDocument();
  });

  test('password fields are initially password type', () => {
    renderPage();
    expect(screen.getByLabelText('New Password')).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText('Confirm Password')).toHaveAttribute('type', 'password');
  });
});

describe('Password visibility toggle', () => {
  test('toggles password field visibility', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    const showBtn = screen.getByRole('button', { name: 'Show password' });

    expect(passwordInput).toHaveAttribute('type', 'password');
    await userEvent.click(showBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: 'Hide password' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('toggles confirm password field visibility', async () => {
    renderPage();
    const confirmInput = screen.getByLabelText('Confirm Password');
    const showBtn = screen.getByRole('button', { name: 'Show confirm password' });

    expect(confirmInput).toHaveAttribute('type', 'password');
    await userEvent.click(showBtn);
    expect(confirmInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: 'Hide confirm password' })).toBeInTheDocument();
  });
});

describe('Validation — on blur', () => {
  test('shows error when password field is blurred empty', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    fireEvent.blur(passwordInput);
    expect(await screen.findByText('Password is required.')).toBeInTheDocument();
  });

  test('shows error when password is too short', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    await userEvent.type(passwordInput, 'Ab1');
    fireEvent.blur(passwordInput);
    expect(await screen.findByText('Password must be at least 8 characters.')).toBeInTheDocument();
  });

  test('shows error when password lacks uppercase', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    await userEvent.type(passwordInput, 'lowercase1');
    fireEvent.blur(passwordInput);
    expect(await screen.findByText('Password must contain at least one uppercase letter.')).toBeInTheDocument();
  });

  test('shows error when password lacks lowercase', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    await userEvent.type(passwordInput, 'UPPERCASE1');
    fireEvent.blur(passwordInput);
    expect(await screen.findByText('Password must contain at least one lowercase letter.')).toBeInTheDocument();
  });

  test('shows error when password lacks a number', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    await userEvent.type(passwordInput, 'NoNumbers!');
    // No digit, no uppercase error should be gone, lowercase present
    fireEvent.blur(passwordInput);
    expect(await screen.findByText('Password must contain at least one number.')).toBeInTheDocument();
  });

  test('shows error when confirm password is blurred empty', async () => {
    renderPage();
    const confirmInput = screen.getByLabelText('Confirm Password');
    fireEvent.blur(confirmInput);
    expect(await screen.findByText('Please confirm your password.')).toBeInTheDocument();
  });

  test('shows mismatch error when passwords differ', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm Password');
    await userEvent.type(passwordInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'DifferentPass1');
    fireEvent.blur(confirmInput);
    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument();
  });
});

describe('Validation — on submit', () => {
  test('shows all errors when submitted with empty fields', async () => {
    renderPage();
    const submitBtn = screen.getByRole('button', { name: /Reset Password/i });
    await userEvent.click(submitBtn);
    expect(await screen.findByText('Password is required.')).toBeInTheDocument();
    expect(await screen.findByText('Please confirm your password.')).toBeInTheDocument();
  });

  test('does not call resetPassword API when form has errors', async () => {
    renderPage();
    const submitBtn = screen.getByRole('button', { name: /Reset Password/i });
    await userEvent.click(submitBtn);
    expect(mockedResetPassword).not.toHaveBeenCalled();
  });
});

describe('Missing token', () => {
  test('shows banner error when token is absent', async () => {
    renderPage(''); // no token in URL
    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm Password');
    await userEvent.type(passwordInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    fireEvent.blur(passwordInput);
    fireEvent.blur(confirmInput);
    const submitBtn = screen.getByRole('button', { name: /Reset Password/i });
    await userEvent.click(submitBtn);
    expect(await screen.findByText(/Reset token is missing or invalid/i)).toBeInTheDocument();
    expect(mockedResetPassword).not.toHaveBeenCalled();
  });
});

describe('Successful submission', () => {
  test('calls resetPassword with correct payload', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset successfully.' });
    renderPage('?token=abc123');
    const passwordInput = screen.getByLabelText('New Password');
    const confirmInput = screen.getByLabelText('Confirm Password');
    await userEvent.type(passwordInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    const submitBtn = screen.getByRole('button', { name: /Reset Password/i });
    await userEvent.click(submitBtn);
    await waitFor(() => {
      expect(mockedResetPassword).toHaveBeenCalledWith({
        token: 'abc123',
        password: 'ValidPass1',
        confirmPassword: 'ValidPass1',
      });
    });
  });

  test('shows success banner after successful reset', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset successfully.' });
    renderPage('?token=abc123');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    expect(await screen.findByText(/Your password has been reset successfully/i)).toBeInTheDocument();
  });

  test('hides form after successful reset', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset successfully.' });
    renderPage('?token=abc123');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Reset Password/i })).not.toBeInTheDocument();
    });
  });

  test('navigates to /login after 3 seconds on success', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset successfully.' });
    renderPage('?token=abc123');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    await screen.findByText(/Your password has been reset successfully/i);
    expect(mockNavigate).not.toHaveBeenCalled();
    act(() => { jest.advanceTimersByTime(3000); });
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});

describe('Failed submission', () => {
  test('shows API error message from response', async () => {
    mockedResetPassword.mockRejectedValueOnce({
      response: {
        data: {
          error: { message: 'Token has expired.' },
        },
      },
    });
    renderPage('?token=expired-token');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    expect(await screen.findByText('Token has expired.')).toBeInTheDocument();
  });

  test('shows fallback error message when response has no message', async () => {
    mockedResetPassword.mockRejectedValueOnce({
      response: { data: {} },
    });
    renderPage('?token=some-token');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    expect(await screen.findByText('An error occurred. Please try again.')).toBeInTheDocument();
  });

  test('shows fallback error message on non-axios error', async () => {
    mockedResetPassword.mockRejectedValueOnce(new Error('Network error'));
    renderPage('?token=some-token');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    expect(await screen.findByText('An error occurred. Please try again.')).toBeInTheDocument();
  });

  test('form remains visible after error', async () => {
    mockedResetPassword.mockRejectedValueOnce(new Error('fail'));
    renderPage('?token=some-token');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    await screen.findByText('An error occurred. Please try again.');
    expect(screen.getByRole('button', { name: /Reset Password/i })).toBeInTheDocument();
  });
});

describe('Submitting state', () => {
  test('button shows loading state while submitting', async () => {
    let resolveReset: (v: { message: string }) => void;
    mockedResetPassword.mockReturnValueOnce(
      new Promise(res => { resolveReset = res; })
    );
    renderPage('?token=abc123');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    expect(await screen.findByText(/Resetting/i)).toBeInTheDocument();
    act(() => resolveReset({ message: 'ok' }));
  });

  test('inputs are disabled while submitting', async () => {
    let resolveReset: (v: { message: string }) => void;
    mockedResetPassword.mockReturnValueOnce(
      new Promise(res => { resolveReset = res; })
    );
    renderPage('?token=abc123');
    await userEvent.type(screen.getByLabelText('New Password'), 'ValidPass1');
    await userEvent.type(screen.getByLabelText('Confirm Password'), 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /Reset Password/i }));
    await screen.findByText(/Resetting/i);
    expect(screen.getByLabelText('New Password')).toBeDisabled();
    expect(screen.getByLabelText('Confirm Password')).toBeDisabled();
    act(() => resolveReset({ message: 'ok' }));
  });
});

describe('Password strength indicator', () => {
  test('shows strength label when password is typed and no error', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    await userEvent.type(passwordInput, 'Ab');
    // 2 criteria met (uppercase + lowercase), length < 8 so strength = 2 but minLength fails
    // Actually minLength needs >=8 chars; 'Ab' has length 2 → minLength fails
    // hasUppercase passes, hasLowercase passes, hasNumber fails → strength = 2
    // But no blur so no error — strength indicator should show
    expect(screen.getByText(/Password strength:/i)).toBeInTheDocument();
  });

  test('does not show strength indicator when password is empty', async () => {
    renderPage();
    expect(screen.queryByText(/Password strength:/i)).not.toBeInTheDocument();
  });

  test('does not show strength when error is visible', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    await userEvent.type(passwordInput, 'Ab');
    fireEvent.blur(passwordInput);
    // Should show error not strength
    await screen.findByText('Password must be at least 8 characters.');
    expect(screen.queryByText(/Password strength:/i)).not.toBeInTheDocument();
  });

  test('shows correct strength label for strong password', async () => {
    renderPage();
    const passwordInput = screen.getByLabelText('New Password');
    // All 4 criteria: length>=8, uppercase, lowercase, number
    await userEvent.type(passwordInput, 'ValidPass1');
    expect(screen.getByText('Password strength: Strong')).toBeInTheDocument();
  });
});

describe('auth.ts resetPassword API', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  test('makes POST to /api/auth/reset-password with correct body', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ message: 'Password reset.' }),
    });
    global.fetch = mockFetch;

    const { resetPassword } = await import('../../../api/auth');
    await resetPassword({ token: 'tok', password: 'pass', confirmPassword: 'pass' });

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/auth/reset-password',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ token: 'tok', password: 'pass', confirm_password: 'pass' }),
      })
    );
  });

  test('throws error data when response is not ok', async () => {
    const errorPayload = { error: { code: 'INVALID_TOKEN', message: 'Token expired.' } };
    const mockFetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => errorPayload,
    });
    global.fetch = mockFetch;

    const { resetPassword } = await import('../../../api/auth');
    await expect(resetPassword({ token: 'bad', password: 'pass', confirmPassword: 'pass' }))
      .rejects.toEqual(errorPayload);
  });

  test('throws generic error when JSON parse fails', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw new SyntaxError('bad json'); },
    });
    global.fetch = mockFetch;

    const { resetPassword } = await import('../../../api/auth');
    await expect(resetPassword({ token: 'tok', password: 'pass', confirmPassword: 'pass' }))
      .rejects.toThrow('HTTP error 500');
  });

  test('returns message response on success', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ message: 'Done.' }),
    });
    global.fetch = mockFetch;

    const { resetPassword } = await import('../../../api/auth');
    const result = await resetPassword({ token: 'tok', password: 'Pass1word', confirmPassword: 'Pass1word' });
    expect(result).toEqual({ message: 'Done.' });
  });
});
