import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PasswordField from './PasswordField';

describe('PasswordField', () => {
  const baseProps = {
    id: 'pwd',
    label: 'Password',
    value: '',
    onChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the label', () => {
    render(<PasswordField {...baseProps} />);
    expect(screen.getByText('Password')).toBeTruthy();
  });

  it('associates label with input', () => {
    render(<PasswordField {...baseProps} />);
    const input = document.getElementById('pwd');
    expect(input).toBeTruthy();
  });

  it('defaults to password type (hidden)', () => {
    render(<PasswordField {...baseProps} />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.type).toBe('password');
  });

  it('shows toggle button with "Show password" label initially', () => {
    render(<PasswordField {...baseProps} />);
    expect(screen.getByRole('button', { name: 'Show password' })).toBeTruthy();
  });

  it('toggles to text type when toggle button clicked', () => {
    render(<PasswordField {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.type).toBe('text');
  });

  it('toggle button label becomes "Hide password" after showing', () => {
    render(<PasswordField {...baseProps} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(screen.getByRole('button', { name: 'Hide password' })).toBeTruthy();
  });

  it('toggles back to password type on second click', () => {
    render(<PasswordField {...baseProps} />);
    const toggle = screen.getByRole('button', { name: 'Show password' });
    fireEvent.click(toggle);
    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.type).toBe('password');
  });

  it('calls onChange with the input value', () => {
    const onChange = jest.fn();
    render(<PasswordField {...baseProps} onChange={onChange} />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'secret' } });
    expect(onChange).toHaveBeenCalledWith('secret');
  });

  it('displays the current value', () => {
    render(<PasswordField {...baseProps} value="mypass" />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.value).toBe('mypass');
  });

  it('shows required asterisk when required', () => {
    render(<PasswordField {...baseProps} required />);
    expect(screen.getByText('*', { exact: false })).toBeTruthy();
  });

  it('shows error message when error provided', () => {
    render(<PasswordField {...baseProps} error="Password too short" />);
    expect(screen.getByText('Password too short')).toBeTruthy();
  });

  it('error span has role="alert"', () => {
    render(<PasswordField {...baseProps} error="Error" />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('adds field--error class when error present', () => {
    const { container } = render(<PasswordField {...baseProps} error="err" />);
    expect(container.querySelector('.field--error')).toBeTruthy();
  });

  it('shows hint text when provided and no error', () => {
    render(<PasswordField {...baseProps} hint="At least 8 chars" />);
    expect(screen.getByText('At least 8 chars')).toBeTruthy();
  });

  it('hides hint when error is present', () => {
    render(<PasswordField {...baseProps} hint="hint" error="err" />);
    expect(screen.queryByText('hint')).toBeNull();
  });

  it('sets aria-invalid when error present', () => {
    render(<PasswordField {...baseProps} error="err" />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.getAttribute('aria-invalid')).toBe('true');
  });

  it('does not set aria-invalid without error', () => {
    render(<PasswordField {...baseProps} />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.getAttribute('aria-invalid')).toBeNull();
  });

  it('sets aria-describedby to error id when error present', () => {
    render(<PasswordField {...baseProps} error="err" />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.getAttribute('aria-describedby')).toBe('pwd-error');
  });

  it('disables both input and toggle when disabled', () => {
    render(<PasswordField {...baseProps} disabled />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.disabled).toBe(true);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('passes placeholder to input', () => {
    render(<PasswordField {...baseProps} placeholder="Enter password" />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.getAttribute('placeholder')).toBe('Enter password');
  });

  it('passes autoComplete to input', () => {
    render(<PasswordField {...baseProps} autoComplete="current-password" />);
    const input = document.getElementById('pwd') as HTMLInputElement;
    expect(input.getAttribute('autocomplete')).toBe('current-password');
  });
});
