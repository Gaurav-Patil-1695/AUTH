// Client-side mirror of validation-rules.md
// Rule order and exact messages match the server-side rules verbatim.

// Password policy mirrors capabilities.yaml:
// min_length: 8, require_uppercase: true, require_lowercase: true,
// require_number: true, require_special_character: false
export const PASSWORD_POLICY = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumber: true,
  requireSpecial: false,
} as const;

// ---------------------------------------------------------------------------
// Validation result
// ---------------------------------------------------------------------------
export interface FieldError {
  field: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: FieldError[];
}

// ---------------------------------------------------------------------------
// Individual field validators — messages copied VERBATIM from validation-rules.md
// ---------------------------------------------------------------------------

export function validateFullName(fullName: string): string | null {
  if (!fullName || fullName.trim().length === 0) {
    return 'Full name is required.';
  }
  if (fullName.trim().length < 2) {
    return 'Full name must be at least 2 characters.';
  }
  if (fullName.trim().length > 100) {
    return 'Full name must not exceed 100 characters.';
  }
  return null;
}

export function validateEmail(email: string): string | null {
  if (!email || email.trim().length === 0) {
    return 'Email is required.';
  }
  // RFC 5322-ish simple check consistent with server
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email.trim())) {
    return 'Enter a valid email address.';
  }
  return null;
}

export function validatePassword(password: string): string | null {
  if (!password || password.length === 0) {
    return 'Password is required.';
  }
  if (password.length < PASSWORD_POLICY.minLength) {
    return 'Password must be at least 8 characters.';
  }
  if (PASSWORD_POLICY.requireUppercase && !/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter.';
  }
  if (PASSWORD_POLICY.requireLowercase && !/[a-z]/.test(password)) {
    return 'Password must contain at least one lowercase letter.';
  }
  if (PASSWORD_POLICY.requireNumber && !/[0-9]/.test(password)) {
    return 'Password must contain at least one number.';
  }
  return null;
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): string | null {
  if (!confirmPassword || confirmPassword.length === 0) {
    return 'Please confirm your password.';
  }
  if (password !== confirmPassword) {
    return 'Passwords do not match.';
  }
  return null;
}

export function validateTerms(accepted: boolean): string | null {
  if (!accepted) {
    return 'You must accept the Terms of Service to continue.';
  }
  return null;
}

// ---------------------------------------------------------------------------
// Password strength — checks the four active policy rules
// (special character is NOT required per config)
// ---------------------------------------------------------------------------
export interface PasswordStrength {
  score: number; // 0-4
  passedRules: PasswordRule[];
  failedRules: PasswordRule[];
}

export interface PasswordRule {
  key: string;
  label: string;
  passed: boolean;
}

export function checkPasswordStrength(password: string): PasswordStrength {
  const rules: Array<{ key: string; label: string; test: (p: string) => boolean }> = [
    {
      key: 'minLength',
      label: 'At least 8 characters',
      test: (p) => p.length >= PASSWORD_POLICY.minLength,
    },
    {
      key: 'uppercase',
      label: 'At least one uppercase letter',
      test: (p) => /[A-Z]/.test(p),
    },
    {
      key: 'lowercase',
      label: 'At least one lowercase letter',
      test: (p) => /[a-z]/.test(p),
    },
    {
      key: 'number',
      label: 'At least one number',
      test: (p) => /[0-9]/.test(p),
    },
  ];

  const evaluated: PasswordRule[] = rules.map((rule) => ({
    key: rule.key,
    label: rule.label,
    passed: rule.test(password),
  }));

  const passedRules = evaluated.filter((r) => r.passed);
  const failedRules = evaluated.filter((r) => !r.passed);

  return {
    score: passedRules.length,
    passedRules,
    failedRules,
  };
}

// ---------------------------------------------------------------------------
// Form-level validators
// ---------------------------------------------------------------------------

export function validateLoginForm(values: {
  email: string;
  password: string;
}): ValidationResult {
  const errors: FieldError[] = [];

  const emailError = validateEmail(values.email);
  if (emailError) errors.push({ field: 'email', message: emailError });

  const passwordError = validatePassword(values.password);
  if (passwordError) errors.push({ field: 'password', message: passwordError });

  return { valid: errors.length === 0, errors };
}

export function validateRegisterForm(values: {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}): ValidationResult {
  const errors: FieldError[] = [];

  const fullNameError = validateFullName(values.fullName);
  if (fullNameError) errors.push({ field: 'fullName', message: fullNameError });

  const emailError = validateEmail(values.email);
  if (emailError) errors.push({ field: 'email', message: emailError });

  const passwordError = validatePassword(values.password);
  if (passwordError) errors.push({ field: 'password', message: passwordError });

  const confirmPasswordError = validateConfirmPassword(
    values.password,
    values.confirmPassword,
  );
  if (confirmPasswordError)
    errors.push({ field: 'confirmPassword', message: confirmPasswordError });

  const termsError = validateTerms(values.acceptTerms);
  if (termsError) errors.push({ field: 'acceptTerms', message: termsError });

  return { valid: errors.length === 0, errors };
}

export function validateForgotPasswordForm(values: {
  email: string;
}): ValidationResult {
  const errors: FieldError[] = [];

  const emailError = validateEmail(values.email);
  if (emailError) errors.push({ field: 'email', message: emailError });

  return { valid: errors.length === 0, errors };
}

export function validateResetPasswordForm(values: {
  password: string;
  confirmPassword: string;
}): ValidationResult {
  const errors: FieldError[] = [];

  const passwordError = validatePassword(values.password);
  if (passwordError) errors.push({ field: 'password', message: passwordError });

  const confirmPasswordError = validateConfirmPassword(
    values.password,
    values.confirmPassword,
  );
  if (confirmPasswordError)
    errors.push({ field: 'confirmPassword', message: confirmPasswordError });

  return { valid: errors.length === 0, errors };
}

// ---------------------------------------------------------------------------
// Utility: extract a single field's error from a result
// ---------------------------------------------------------------------------
export function getFieldError(
  result: ValidationResult,
  field: string,
): string | undefined {
  return result.errors.find((e) => e.field === field)?.message;
}
