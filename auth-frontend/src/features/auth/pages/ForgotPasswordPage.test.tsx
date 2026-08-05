import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ForgotPasswordPage from './ForgotPasswordPage';
import * as authApi from '../../../api/auth';

vi.mock('../../../api/auth', () => ({
  forgotPassword: vi.fn(),
}));

const renderPage = () =>
  render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>,
  );

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders the page title', () => {
    renderPage();
    expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument();
  });

  it('renders the email input', () => {
    renderPage();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  it('renders the submit button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
  });

  it('renders a link to the sign in page', () => {
    renderPage();
    const link = screen.getByRole('link', { name: /sign in/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/login');
  });

  it('renders the branding logo', () => {
    renderPage();
    expect(screen.getByText('auth-starter')).toBeInTheDocument();
  });

  // ── Email validation on blur ───────────────────────────────────────────────

  it('shows required error when blurring an empty email field', async () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    fireEvent.blur(input);
    expect(await screen.findByText('Email is required.')).toBeInTheDocument();
  });

  it('shows invalid-email error when blurring with a bad email', async () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    await userEvent.type(input, 'not-an-email');
    fireEvent.blur(input);
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument();
  });

  it('clears the error when user starts correcting the email', async () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    fireEvent.blur(input); // triggers required error
    await screen.findByText('Email is required.');
    await userEvent.type(input, 'good@example.com');
    expect(screen.queryByText('Email is required.')).not.toBeInTheDocument();
  });

  // ── Submit validation ──────────────────────────────────────────────────────

  it('shows required error on submit with empty field without calling api', async () => {
    renderPage();
    const button = screen.getByRole('button', { name: /send reset link/i });
    await userEvent.click(button);
    expect(await screen.findByText('Email is required.')).toBeInTheDocument();
    expect(authApi.forgotPassword).not.toHaveBeenCalled();
  });

  it('shows invalid-email error on submit with malformed email without calling api', async () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    await userEvent.type(input, 'bad@@email');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument();
    expect(authApi.forgotPassword).not.toHaveBeenCalled();
  });

  // ── Successful submission ──────────────────────────────────────────────────

  it('calls forgotPassword with trimmed email on valid submit', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValueOnce({ message: 'ok' });
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), '  test@example.com  ');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    await waitFor(() =>
      expect(authApi.forgotPassword).toHaveBeenCalledWith({ email: 'test@example.com' }),
    );
  });

  it('hides the form and shows success banner after successful submission', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValueOnce({ message: 'ok' });
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    await waitFor(() =>
      expect(
        screen.getByText(/if an account with that email exists/i),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByRole('button', { name: /send reset link/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/email address/i)).not.toBeInTheDocument();
  });

  it('success banner has role status', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValueOnce({ message: 'ok' });
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    const banner = await screen.findByRole('status');
    expect(banner).toBeInTheDocument();
  });

  // ── Failed submission ──────────────────────────────────────────────────────

  it('shows a banner error when the api call throws', async () => {
    vi.mocked(authApi.forgotPassword).mockRejectedValueOnce(new Error('server error'));
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    expect(
      await screen.findByText(/something went wrong/i),
    ).toBeInTheDocument();
  });

  it('banner error has role alert', async () => {
    vi.mocked(authApi.forgotPassword).mockRejectedValueOnce(new Error('server error'));
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    const alert = await screen.findByRole('alert');
    expect(alert).toBeInTheDocument();
  });

  it('keeps the form visible after a failed submission', async () => {
    vi.mocked(authApi.forgotPassword).mockRejectedValueOnce(new Error('server error'));
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    await waitFor(() => screen.findByText(/something went wrong/i));
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  // ── Loading state ──────────────────────────────────────────────────────────

  it('disables the submit button while submitting', async () => {
    let resolveApi!: () => void;
    vi.mocked(authApi.forgotPassword).mockReturnValueOnce(
      new Promise<{ message: string }>((resolve) => {
        resolveApi = () => resolve({ message: 'ok' });
      }),
    );
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    const button = screen.getByRole('button', { name: /sending/i });
    expect(button).toBeDisabled();
    resolveApi();
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /sending/i })).not.toBeInTheDocument(),
    );
  });

  it('disables the email input while submitting', async () => {
    let resolveApi!: () => void;
    vi.mocked(authApi.forgotPassword).mockReturnValueOnce(
      new Promise<{ message: string }>((resolve) => {
        resolveApi = () => resolve({ message: 'ok' });
      }),
    );
    renderPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'test@example.com');
    await userEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    expect(screen.getByLabelText(/email address/i)).toBeDisabled();
    resolveApi();
  });

  // ── Inline error aria attributes ───────────────────────────────────────────

  it('marks the input as aria-invalid when there is an email error', async () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    fireEvent.blur(input);
    await screen.findByText('Email is required.');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('sets aria-describedby on the input when there is an email error', async () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    fireEvent.blur(input);
    await screen.findByText('Email is required.');
    expect(input).toHaveAttribute('aria-describedby', 'email-error');
  });

  it('sets aria-invalid to false when there is no email error', () => {
    renderPage();
    const input = screen.getByLabelText(/email address/i);
    expect(input).toHaveAttribute('aria-invalid', 'false');
  });
});
