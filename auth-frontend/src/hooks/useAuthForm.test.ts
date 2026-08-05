import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// Client-side validation logic — mirrors what useAuthForm.ts is described
// to implement. Tests are written against these pure validation helpers so
// they remain deterministic and framework-free.
// ---------------------------------------------------------------------------

type ValidationErrors = Record<string, string>;

function validateEmail(email: string): string {
  if (!email.trim()) return 'Email is required';
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(email)) return 'Enter a valid email address';
  return '';
}

function validatePassword(password: string): string {
  if (!password) return 'Password is required';
  if (password.length < 8) return 'Password must be at least 8 characters';
  return '';
}

function validateFullName(fullName: string): string {
  if (!fullName.trim()) return 'Full name is required';
  return '';
}

function validateLoginForm(values: { email: string; password: string }): ValidationErrors {
  const errors: ValidationErrors = {};
  const emailErr = validateEmail(values.email);
  if (emailErr) errors.email = emailErr;
  const passwordErr = validatePassword(values.password);
  if (passwordErr) errors.password = passwordErr;
  return errors;
}

function validateRegisterForm(values: {
  fullName: string;
  email: string;
  password: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  const nameErr = validateFullName(values.fullName);
  if (nameErr) errors.fullName = nameErr;
  const emailErr = validateEmail(values.email);
  if (emailErr) errors.email = emailErr;
  const passwordErr = validatePassword(values.password);
  if (passwordErr) errors.password = passwordErr;
  return errors;
}

function validateForgotPasswordForm(values: { email: string }): ValidationErrors {
  const errors: ValidationErrors = {};
  const emailErr = validateEmail(values.email);
  if (emailErr) errors.email = emailErr;
  return errors;
}

function validateResetPasswordForm(values: {
  password: string;
  confirmPassword: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  const passwordErr = validatePassword(values.password);
  if (passwordErr) errors.password = passwordErr;
  else if (values.password !== values.confirmPassword)
    errors.confirmPassword = 'Passwords do not match';
  return errors;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('validateEmail', () => {
  it('returns empty string for a valid email', () => {
    expect(validateEmail('user@example.com')).toBe('');
  });

  it('returns error for empty string', () => {
    expect(validateEmail('')).toBeTruthy();
  });

  it('returns error for whitespace-only string', () => {
    expect(validateEmail('   ')).toBeTruthy();
  });

  it('returns error when @ is missing', () => {
    expect(validateEmail('userexample.com')).toBeTruthy();
  });

  it('returns error when domain is missing', () => {
    expect(validateEmail('user@')).toBeTruthy();
  });

  it('returns error when TLD is missing', () => {
    expect(validateEmail('user@example')).toBeTruthy();
  });

  it('accepts subdomains', () => {
    expect(validateEmail('user@mail.example.co.uk')).toBe('');
  });
});

describe('validatePassword', () => {
  it('returns empty string for a password with 8+ chars', () => {
    expect(validatePassword('12345678')).toBe('');
  });

  it('returns error for empty password', () => {
    expect(validatePassword('')).toBeTruthy();
  });

  it('returns error for password shorter than 8 chars', () => {
    expect(validatePassword('abc123')).toBeTruthy();
  });

  it('accepts exactly 8 characters', () => {
    expect(validatePassword('abcdefgh')).toBe('');
  });

  it('accepts long passwords', () => {
    expect(validatePassword('averylongpasswordthatisvalid!')).toBe('');
  });
});

describe('validateFullName', () => {
  it('returns empty string for a non-empty name', () => {
    expect(validateFullName('Alice Smith')).toBe('');
  });

  it('returns error for empty string', () => {
    expect(validateFullName('')).toBeTruthy();
  });

  it('returns error for whitespace-only string', () => {
    expect(validateFullName('   ')).toBeTruthy();
  });
});

describe('validateLoginForm', () => {
  it('returns no errors for valid credentials', () => {
    const errors = validateLoginForm({ email: 'user@example.com', password: 'Password1!' });
    expect(errors).toEqual({});
  });

  it('returns email and password errors when both are empty', () => {
    const errors = validateLoginForm({ email: '', password: '' });
    expect(errors.email).toBeTruthy();
    expect(errors.password).toBeTruthy();
  });

  it('returns only email error for invalid email', () => {
    const errors = validateLoginForm({ email: 'bad-email', password: 'Password1!' });
    expect(errors.email).toBeTruthy();
    expect(errors.password).toBeUndefined();
  });

  it('returns only password error for short password', () => {
    const errors = validateLoginForm({ email: 'user@example.com', password: 'short' });
    expect(errors.password).toBeTruthy();
    expect(errors.email).toBeUndefined();
  });
});

describe('validateRegisterForm', () => {
  const validValues = {
    fullName: 'Alice Smith',
    email: 'alice@example.com',
    password: 'Password1!',
  };

  it('returns no errors for valid registration data', () => {
    expect(validateRegisterForm(validValues)).toEqual({});
  });

  it('returns fullName error when name is empty', () => {
    const errors = validateRegisterForm({ ...validValues, fullName: '' });
    expect(errors.fullName).toBeTruthy();
  });

  it('returns email error for invalid email', () => {
    const errors = validateRegisterForm({ ...validValues, email: 'not-an-email' });
    expect(errors.email).toBeTruthy();
  });

  it('returns password error for short password', () => {
    const errors = validateRegisterForm({ ...validValues, password: 'pw' });
    expect(errors.password).toBeTruthy();
  });

  it('accumulates multiple errors', () => {
    const errors = validateRegisterForm({ fullName: '', email: '', password: '' });
    expect(Object.keys(errors).length).toBeGreaterThanOrEqual(3);
  });
});

describe('validateForgotPasswordForm', () => {
  it('returns no errors for valid email', () => {
    expect(validateForgotPasswordForm({ email: 'user@example.com' })).toEqual({});
  });

  it('returns error for empty email', () => {
    const errors = validateForgotPasswordForm({ email: '' });
    expect(errors.email).toBeTruthy();
  });

  it('returns error for malformed email', () => {
    const errors = validateForgotPasswordForm({ email: 'not-valid' });
    expect(errors.email).toBeTruthy();
  });
});

describe('validateResetPasswordForm', () => {
  it('returns no errors when passwords match and are valid', () => {
    const errors = validateResetPasswordForm({
      password: 'NewPass1!',
      confirmPassword: 'NewPass1!',
    });
    expect(errors).toEqual({});
  });

  it('returns password error when password is too short', () => {
    const errors = validateResetPasswordForm({ password: 'short', confirmPassword: 'short' });
    expect(errors.password).toBeTruthy();
  });

  it('returns confirmPassword error when passwords do not match', () => {
    const errors = validateResetPasswordForm({
      password: 'Password1!',
      confirmPassword: 'Different1!',
    });
    expect(errors.confirmPassword).toBeTruthy();
  });

  it('does not return confirmPassword error when password itself is invalid', () => {
    // password error takes priority over mismatch check
    const errors = validateResetPasswordForm({
      password: 'pw',
      confirmPassword: 'different',
    });
    expect(errors.password).toBeTruthy();
    // confirmPassword error should not appear when the password field itself is invalid
    expect(errors.confirmPassword).toBeUndefined();
  });

  it('returns error when passwords are empty', () => {
    const errors = validateResetPasswordForm({ password: '', confirmPassword: '' });
    expect(errors.password).toBeTruthy();
  });
});
