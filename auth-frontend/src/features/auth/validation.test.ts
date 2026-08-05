import {
  PASSWORD_POLICY,
  validateFullName,
  validateEmail,
  validatePassword,
  validateConfirmPassword,
  validateTerms,
  checkPasswordStrength,
  validateLoginForm,
  validateRegisterForm,
  validateForgotPasswordForm,
  validateResetPasswordForm,
  getFieldError,
} from './validation';

// ---------------------------------------------------------------------------
// PASSWORD_POLICY constant
// ---------------------------------------------------------------------------
describe('PASSWORD_POLICY', () => {
  it('has the correct shape', () => {
    expect(PASSWORD_POLICY.minLength).toBe(8);
    expect(PASSWORD_POLICY.requireUppercase).toBe(true);
    expect(PASSWORD_POLICY.requireLowercase).toBe(true);
    expect(PASSWORD_POLICY.requireNumber).toBe(true);
    expect(PASSWORD_POLICY.requireSpecial).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// validateFullName
// ---------------------------------------------------------------------------
describe('validateFullName', () => {
  it('returns error for empty string', () => {
    expect(validateFullName('')).toBe('Full name is required.');
  });

  it('returns error for whitespace-only string', () => {
    expect(validateFullName('   ')).toBe('Full name is required.');
  });

  it('returns error for single character', () => {
    expect(validateFullName('A')).toBe('Full name must be at least 2 characters.');
  });

  it('returns error for single character surrounded by spaces', () => {
    expect(validateFullName(' A ')).toBe('Full name must be at least 2 characters.');
  });

  it('returns error for name exceeding 100 characters', () => {
    const longName = 'A'.repeat(101);
    expect(validateFullName(longName)).toBe('Full name must not exceed 100 characters.');
  });

  it('returns null for exactly 2 characters', () => {
    expect(validateFullName('AB')).toBeNull();
  });

  it('returns null for exactly 100 characters', () => {
    expect(validateFullName('A'.repeat(100))).toBeNull();
  });

  it('returns null for a normal name', () => {
    expect(validateFullName('John Doe')).toBeNull();
  });

  it('returns null for name with leading/trailing spaces that is valid after trim', () => {
    expect(validateFullName('  John  ')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// validateEmail
// ---------------------------------------------------------------------------
describe('validateEmail', () => {
  it('returns error for empty string', () => {
    expect(validateEmail('')).toBe('Email is required.');
  });

  it('returns error for whitespace-only string', () => {
    expect(validateEmail('   ')).toBe('Email is required.');
  });

  it('returns error for string without @', () => {
    expect(validateEmail('notanemail')).toBe('Enter a valid email address.');
  });

  it('returns error for string without domain', () => {
    expect(validateEmail('user@')).toBe('Enter a valid email address.');
  });

  it('returns error for string without TLD', () => {
    expect(validateEmail('user@domain')).toBe('Enter a valid email address.');
  });

  it('returns error for email with spaces', () => {
    expect(validateEmail('user @domain.com')).toBe('Enter a valid email address.');
  });

  it('returns null for valid email', () => {
    expect(validateEmail('user@example.com')).toBeNull();
  });

  it('returns null for valid email with leading/trailing spaces', () => {
    expect(validateEmail('  user@example.com  ')).toBeNull();
  });

  it('returns null for valid email with subdomain', () => {
    expect(validateEmail('user@mail.example.com')).toBeNull();
  });

  it('returns null for valid email with plus', () => {
    expect(validateEmail('user+tag@example.com')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// validatePassword
// ---------------------------------------------------------------------------
describe('validatePassword', () => {
  it('returns error for empty string', () => {
    expect(validatePassword('')).toBe('Password is required.');
  });

  it('returns error for password shorter than 8 characters', () => {
    expect(validatePassword('Ab1')).toBe('Password must be at least 8 characters.');
  });

  it('returns error for password of exactly 7 characters', () => {
    expect(validatePassword('Abcde1f')).toBe('Password must be at least 8 characters.');
  });

  it('returns error when no uppercase letter', () => {
    expect(validatePassword('abcde123')).toBe('Password must contain at least one uppercase letter.');
  });

  it('returns error when no lowercase letter', () => {
    expect(validatePassword('ABCDE123')).toBe('Password must contain at least one lowercase letter.');
  });

  it('returns error when no number', () => {
    expect(validatePassword('Abcdefgh')).toBe('Password must contain at least one number.');
  });

  it('returns null for valid password meeting all requirements', () => {
    expect(validatePassword('Abcde123')).toBeNull();
  });

  it('returns null for password with special characters (not required but allowed)', () => {
    expect(validatePassword('Abcde1@!')).toBeNull();
  });

  it('returns null for exactly 8-character valid password', () => {
    expect(validatePassword('Abcde12!')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// validateConfirmPassword
// ---------------------------------------------------------------------------
describe('validateConfirmPassword', () => {
  it('returns error for empty confirmPassword', () => {
    expect(validateConfirmPassword('Abcde123', '')).toBe('Please confirm your password.');
  });

  it('returns error when passwords do not match', () => {
    expect(validateConfirmPassword('Abcde123', 'Abcde124')).toBe('Passwords do not match.');
  });

  it('returns null when passwords match', () => {
    expect(validateConfirmPassword('Abcde123', 'Abcde123')).toBeNull();
  });

  it('returns error for case-mismatched passwords', () => {
    expect(validateConfirmPassword('Abcde123', 'abcde123')).toBe('Passwords do not match.');
  });
});

// ---------------------------------------------------------------------------
// validateTerms
// ---------------------------------------------------------------------------
describe('validateTerms', () => {
  it('returns error when terms not accepted', () => {
    expect(validateTerms(false)).toBe('You must accept the Terms of Service to continue.');
  });

  it('returns null when terms accepted', () => {
    expect(validateTerms(true)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// checkPasswordStrength
// ---------------------------------------------------------------------------
describe('checkPasswordStrength', () => {
  it('returns score 0 for empty password', () => {
    const result = checkPasswordStrength('');
    expect(result.score).toBe(0);
    expect(result.passedRules).toHaveLength(0);
    expect(result.failedRules).toHaveLength(4);
  });

  it('returns score 4 for fully valid password', () => {
    const result = checkPasswordStrength('Abcde123');
    expect(result.score).toBe(4);
    expect(result.passedRules).toHaveLength(4);
    expect(result.failedRules).toHaveLength(0);
  });

  it('returns score 1 for only length satisfied (all lowercase, no number)', () => {
    const result = checkPasswordStrength('abcdefgh');
    // length >= 8: pass, uppercase: fail, lowercase: pass, number: fail => score 2
    expect(result.score).toBe(2);
  });

  it('returns correct passed/failed rule keys', () => {
    const result = checkPasswordStrength('abcde123');
    // length: pass, uppercase: fail, lowercase: pass, number: pass => score 3
    expect(result.score).toBe(3);
    const passedKeys = result.passedRules.map((r) => r.key);
    const failedKeys = result.failedRules.map((r) => r.key);
    expect(passedKeys).toContain('minLength');
    expect(passedKeys).toContain('lowercase');
    expect(passedKeys).toContain('number');
    expect(failedKeys).toContain('uppercase');
  });

  it('includes correct labels', () => {
    const result = checkPasswordStrength('Abcde123');
    const labels = result.passedRules.map((r) => r.label);
    expect(labels).toContain('At least 8 characters');
    expect(labels).toContain('At least one uppercase letter');
    expect(labels).toContain('At least one lowercase letter');
    expect(labels).toContain('At least one number');
  });

  it('returns score 0 for short lowercase-only password', () => {
    const result = checkPasswordStrength('abc');
    // length: fail, uppercase: fail, lowercase: pass, number: fail => score 1
    expect(result.score).toBe(1);
    const passedKeys = result.passedRules.map((r) => r.key);
    expect(passedKeys).toContain('lowercase');
  });

  it('has passed field set correctly on each rule', () => {
    const result = checkPasswordStrength('Abcde123');
    result.passedRules.forEach((r) => expect(r.passed).toBe(true));
    result.failedRules.forEach((r) => expect(r.passed).toBe(false));
  });
});

// ---------------------------------------------------------------------------
// validateLoginForm
// ---------------------------------------------------------------------------
describe('validateLoginForm', () => {
  it('returns valid result for correct credentials', () => {
    const result = validateLoginForm({ email: 'user@example.com', password: 'Abcde123' });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('returns errors for empty email and password', () => {
    const result = validateLoginForm({ email: '', password: '' });
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(2);
  });

  it('returns email error for invalid email', () => {
    const result = validateLoginForm({ email: 'bad', password: 'Abcde123' });
    expect(result.valid).toBe(false);
    const emailError = result.errors.find((e) => e.field === 'email');
    expect(emailError).toBeDefined();
    expect(emailError?.message).toBe('Enter a valid email address.');
  });

  it('returns password error for weak password', () => {
    const result = validateLoginForm({ email: 'user@example.com', password: 'short' });
    expect(result.valid).toBe(false);
    const pwError = result.errors.find((e) => e.field === 'password');
    expect(pwError).toBeDefined();
  });

  it('collects both email and password errors', () => {
    const result = validateLoginForm({ email: 'bademail', password: 'weak' });
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.field === 'email')).toBe(true);
    expect(result.errors.some((e) => e.field === 'password')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// validateRegisterForm
// ---------------------------------------------------------------------------
describe('validateRegisterForm', () => {
  const validValues = {
    fullName: 'John Doe',
    email: 'john@example.com',
    password: 'Abcde123',
    confirmPassword: 'Abcde123',
    acceptTerms: true,
  };

  it('returns valid for all correct fields', () => {
    const result = validateRegisterForm(validValues);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('returns fullName error for empty name', () => {
    const result = validateRegisterForm({ ...validValues, fullName: '' });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'fullName');
    expect(err?.message).toBe('Full name is required.');
  });

  it('returns email error for invalid email', () => {
    const result = validateRegisterForm({ ...validValues, email: 'bad' });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'email');
    expect(err?.message).toBe('Enter a valid email address.');
  });

  it('returns password error for weak password', () => {
    const result = validateRegisterForm({
      ...validValues,
      password: 'weak',
      confirmPassword: 'weak',
    });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'password');
    expect(err).toBeDefined();
  });

  it('returns confirmPassword error when passwords do not match', () => {
    const result = validateRegisterForm({ ...validValues, confirmPassword: 'Different1' });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'confirmPassword');
    expect(err?.message).toBe('Passwords do not match.');
  });

  it('returns terms error when terms not accepted', () => {
    const result = validateRegisterForm({ ...validValues, acceptTerms: false });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'acceptTerms');
    expect(err?.message).toBe('You must accept the Terms of Service to continue.');
  });

  it('returns all errors for completely empty/invalid form', () => {
    const result = validateRegisterForm({
      fullName: '',
      email: '',
      password: '',
      confirmPassword: '',
      acceptTerms: false,
    });
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThanOrEqual(4);
  });
});

// ---------------------------------------------------------------------------
// validateForgotPasswordForm
// ---------------------------------------------------------------------------
describe('validateForgotPasswordForm', () => {
  it('returns valid for valid email', () => {
    const result = validateForgotPasswordForm({ email: 'user@example.com' });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('returns error for empty email', () => {
    const result = validateForgotPasswordForm({ email: '' });
    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0].field).toBe('email');
    expect(result.errors[0].message).toBe('Email is required.');
  });

  it('returns error for invalid email', () => {
    const result = validateForgotPasswordForm({ email: 'notvalid' });
    expect(result.valid).toBe(false);
    expect(result.errors[0].message).toBe('Enter a valid email address.');
  });
});

// ---------------------------------------------------------------------------
// validateResetPasswordForm
// ---------------------------------------------------------------------------
describe('validateResetPasswordForm', () => {
  it('returns valid for matching valid passwords', () => {
    const result = validateResetPasswordForm({
      password: 'Abcde123',
      confirmPassword: 'Abcde123',
    });
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('returns password error for weak password', () => {
    const result = validateResetPasswordForm({
      password: 'weak',
      confirmPassword: 'weak',
    });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'password');
    expect(err).toBeDefined();
  });

  it('returns confirmPassword error when passwords do not match', () => {
    const result = validateResetPasswordForm({
      password: 'Abcde123',
      confirmPassword: 'Abcde124',
    });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'confirmPassword');
    expect(err?.message).toBe('Passwords do not match.');
  });

  it('returns error for empty confirmPassword', () => {
    const result = validateResetPasswordForm({
      password: 'Abcde123',
      confirmPassword: '',
    });
    expect(result.valid).toBe(false);
    const err = result.errors.find((e) => e.field === 'confirmPassword');
    expect(err?.message).toBe('Please confirm your password.');
  });

  it('returns both password and confirmPassword errors for empty inputs', () => {
    const result = validateResetPasswordForm({ password: '', confirmPassword: '' });
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.field === 'password')).toBe(true);
    expect(result.errors.some((e) => e.field === 'confirmPassword')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// getFieldError
// ---------------------------------------------------------------------------
describe('getFieldError', () => {
  const result = {
    valid: false,
    errors: [
      { field: 'email', message: 'Email is required.' },
      { field: 'password', message: 'Password is required.' },
    ],
  };

  it('returns the message for an existing field', () => {
    expect(getFieldError(result, 'email')).toBe('Email is required.');
    expect(getFieldError(result, 'password')).toBe('Password is required.');
  });

  it('returns undefined for a field not in errors', () => {
    expect(getFieldError(result, 'fullName')).toBeUndefined();
  });

  it('returns undefined when errors array is empty', () => {
    expect(getFieldError({ valid: true, errors: [] }, 'email')).toBeUndefined();
  });
});
