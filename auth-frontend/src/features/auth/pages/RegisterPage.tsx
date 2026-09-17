import React, { useState, useId } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../../../api/auth';

interface RegisterFormState {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

interface RegisterFormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  acceptTerms?: string;
}

function getPasswordStrength(password: string): { score: number; labels: string[] } {
  const checks = [
    { label: '8+ characters', pass: password.length >= 8 },
    { label: 'Uppercase', pass: /[A-Z]/.test(password) },
    { label: 'Lowercase', pass: /[a-z]/.test(password) },
    { label: 'Number', pass: /\d/.test(password) },
  ];
  const passed = checks.filter((c) => c.pass);
  return { score: passed.length, labels: checks.map((c) => c.label) };
}

function validateForm(values: RegisterFormState): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!values.fullName || values.fullName.trim().length === 0) {
    errors.fullName = 'Full name is required.';
  } else if (values.fullName.length > 120) {
    errors.fullName = 'Full name is required.';
  }

  if (!values.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!values.password || values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(values.password)) {
    errors.password = 'Password must be at least 8 characters.';
  }

  if (!values.confirmPassword || values.confirmPassword !== values.password) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  if (!values.acceptTerms) {
    errors.acceptTerms = 'You must accept the Terms to continue.';
  }

  return errors;
}

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const baseId = useId();

  const [values, setValues] = useState<RegisterFormState>({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });

  const [errors, setErrors] = useState<RegisterFormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [touched, setTouched] = useState<Partial<Record<keyof RegisterFormState, boolean>>>({});

  const fullNameId = `${baseId}-fullName`;
  const emailId = `${baseId}-email`;
  const passwordId = `${baseId}-password`;
  const confirmPasswordId = `${baseId}-confirmPassword`;
  const acceptTermsId = `${baseId}-acceptTerms`;

  const fullNameErrId = `${fullNameId}-err`;
  const emailErrId = `${emailId}-err`;
  const passwordErrId = `${passwordId}-err`;
  const confirmPasswordErrId = `${confirmPasswordId}-err`;
  const acceptTermsErrId = `${acceptTermsId}-err`;
  const serverErrId = `${baseId}-server-err`;

  const passwordStrength = getPasswordStrength(values.password);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const newValues = {
      ...values,
      [name]: type === 'checkbox' ? checked : value,
    };
    setValues(newValues);
    if (touched[name as keyof RegisterFormState]) {
      const newErrors = validateForm(newValues);
      setErrors((prev) => ({ ...prev, [name]: newErrors[name as keyof RegisterFormErrors] }));
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    const newErrors = validateForm(values);
    setErrors((prev) => ({ ...prev, [name]: newErrors[name as keyof RegisterFormErrors] }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setTouched({ fullName: true, email: true, password: true, confirmPassword: true, acceptTerms: true });
    const validationErrors = validateForm(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }
    setIsSubmitting(true);
    setServerError(null);
    try {
      await register({
        fullName: values.fullName,
        email: values.email,
        password: values.password,
        confirmPassword: values.confirmPassword,
      });
      navigate('/login', { replace: true });
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { error?: { message?: string } } } };
        const msg = axiosErr.response?.data?.error?.message;
        if (msg) {
          setServerError(msg);
        } else {
          setServerError('Registration failed. Please try again.');
        }
      } else {
        setServerError('Registration failed. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const strengthColors = ['#DC2626', '#D97706', '#2563EB', '#16A34A'];
  const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong'];

  return (
    <>
      <style>{`
        :root {
          --color-accent-disabled: #c7d2fe;
          --color-accent-primary: #4f46e5;
          --color-accent-primary-active: #3730a3;
          --color-accent-primary-hover: #4338ca;
          --color-bg-app: #f1f5f9;
          --color-border: #E2E8F0;
          --color-border-strong: #CBD5E1;
          --color-error: #DC2626;
          --color-focus-ring: #818cf8;
          --color-info: #2563EB;
          --color-link: #4f46e5;
          --color-muted-surface: #f8fafc;
          --color-success: #16A34A;
          --color-surface: #FFFFFF;
          --color-text-muted: #94A3B8;
          --color-text-primary: #0F172A;
          --color-text-secondary: #475569;
          --color-warning: #D97706;
          --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
          --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
          --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
          --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --family-mono: 'JetBrains Mono', 'Courier New', monospace;
          --radius-button: 8px;
          --radius-card: 16px;
          --radius-full: 9999px;
          --radius-input: 8px;
          --radius-lg: 12px;
          --radius-sm: 4px;
          --space-2xl: 48px;
          --space-lg: 24px;
          --space-md: 16px;
          --space-sm: 8px;
          --space-xl: 32px;
          --space-xs: 4px;
        }

        .auth-layout {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-lg);
          font-family: var(--family-base);
          color: var(--color-text-primary);
        }

        .auth-branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .auth-branding__logo {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-accent-primary);
          letter-spacing: -0.5px;
        }

        .auth-branding__tagline {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin-top: var(--space-xs);
        }

        .auth-card {
          background: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-2xl);
          width: 100%;
          max-width: 440px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xs) 0;
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin: 0 0 var(--space-xl) 0;
        }

        .auth-card__form {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }

        .auth-card__field {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .auth-card__field label {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-primary);
        }

        .auth-card__field input[type='text'],
        .auth-card__field input[type='email'],
        .auth-card__field input[type='password'] {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-size: 16px;
          font-family: var(--family-base);
          line-height: 1.5;
          color: var(--color-text-primary);
          background: var(--color-muted-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-input);
          outline: none;
          box-sizing: border-box;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .auth-card__field input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .auth-card__field input[aria-invalid='true'] {
          border-color: var(--color-error);
        }

        .field--error input {
          border-color: var(--color-error);
        }

        .field__error {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
          margin: 0;
        }

        .field__password-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .field__password-wrapper input {
          padding-right: 44px;
        }

        .field__password-toggle {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          color: var(--color-text-muted);
          padding: var(--space-xs);
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-sm);
          font-size: 14px;
          line-height: 1;
        }

        .field__password-toggle:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .strength-meter {
          margin-top: var(--space-xs);
        }

        .strength-meter__bars {
          display: flex;
          gap: var(--space-xs);
          margin-bottom: var(--space-xs);
        }

        .strength-meter__bar {
          height: 4px;
          flex: 1;
          border-radius: var(--radius-full);
          background: var(--color-border);
          transition: background 0.2s;
        }

        .strength-meter__label {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-muted);
        }

        .strength-meter__checks {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-xs) var(--space-sm);
          margin-top: var(--space-xs);
        }

        .strength-meter__check {
          font-size: 12px;
          line-height: 1.5;
          color: var(--color-text-muted);
          display: flex;
          align-items: center;
          gap: var(--space-xs);
        }

        .strength-meter__check--pass {
          color: var(--color-success);
        }

        .auth-card__field--checkbox {
          flex-direction: row;
          align-items: flex-start;
          gap: var(--space-sm);
        }

        .auth-card__field--checkbox input[type='checkbox'] {
          width: 16px;
          height: 16px;
          margin-top: 2px;
          flex-shrink: 0;
          cursor: pointer;
          accent-color: var(--color-accent-primary);
        }

        .auth-card__field--checkbox label {
          font-size: 14px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-secondary);
          cursor: pointer;
        }

        .auth-card__submit {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-size: 16px;
          font-weight: 600;
          font-family: var(--family-base);
          line-height: 1.5;
          color: var(--color-surface);
          background: var(--color-accent-primary);
          border: none;
          border-radius: var(--radius-button);
          cursor: pointer;
          transition: background 0.15s;
          margin-top: var(--space-sm);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
        }

        .auth-card__submit:hover:not(:disabled) {
          background: var(--color-accent-primary-hover);
        }

        .auth-card__submit:active:not(:disabled) {
          background: var(--color-accent-primary-active);
        }

        .auth-card__submit:disabled {
          background: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .auth-card__submit:focus-visible {
          outline: none;
          box-shadow: var(--elevation-focus);
        }

        .auth-card__footer {
          margin: var(--space-lg) 0 0 0;
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
        }

        .link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }

        .link:hover {
          text-decoration: underline;
        }

        .auth-card__server-error {
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-input);
          background: #fef2f2;
          border: 1px solid var(--color-error);
          color: var(--color-error);
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          margin: 0;
        }

        .spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className='auth-layout'>
        <div className='auth-branding'>
          <div className='auth-branding__logo'>auth-starter</div>
          <div className='auth-branding__tagline'>Secure authentication, ready to go.</div>
        </div>

        <div className='auth-card' role='main'>
          <h1 className='auth-card__title'>Create account</h1>
          <p className='auth-card__subtitle'>Sign up to get started today.</p>

          {serverError && (
            <div aria-live='polite'>
              <p className='auth-card__server-error' id={serverErrId} role='alert'>
                {serverError}
              </p>
            </div>
          )}

          <form className='auth-card__form' onSubmit={handleSubmit} noValidate>
            {/* Full Name */}
            <div className={`auth-card__field${errors.fullName ? ' field--error' : ''}`}>
              <label htmlFor={fullNameId}>Full name</label>
              <input
                id={fullNameId}
                name='fullName'
                type='text'
                autoComplete='name'
                value={values.fullName}
                onChange={handleChange}
                onBlur={handleBlur}
                aria-describedby={errors.fullName ? fullNameErrId : undefined}
                aria-invalid={errors.fullName ? 'true' : undefined}
                aria-required='true'
                disabled={isSubmitting}
              />
              {errors.fullName && (
                <p className='field__error' id={fullNameErrId} role='alert'>
                  {errors.fullName}
                </p>
              )}
            </div>

            {/* Email */}
            <div className={`auth-card__field${errors.email ? ' field--error' : ''}`}>
              <label htmlFor={emailId}>Email address</label>
              <input
                id={emailId}
                name='email'
                type='email'
                autoComplete='email'
                value={values.email}
                onChange={handleChange}
                onBlur={handleBlur}
                aria-describedby={errors.email ? emailErrId : undefined}
                aria-invalid={errors.email ? 'true' : undefined}
                aria-required='true'
                disabled={isSubmitting}
              />
              {errors.email && (
                <p className='field__error' id={emailErrId} role='alert'>
                  {errors.email}
                </p>
              )}
            </div>

            {/* Password */}
            <div className={`auth-card__field${errors.password ? ' field--error' : ''}`}>
              <label htmlFor={passwordId}>Password</label>
              <div className='field__password-wrapper'>
                <input
                  id={passwordId}
                  name='password'
                  type={showPassword ? 'text' : 'password'}
                  autoComplete='new-password'
                  value={values.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  aria-describedby={
                    [errors.password ? passwordErrId : '', `${baseId}-strength`]
                      .filter(Boolean)
                      .join(' ') || undefined
                  }
                  aria-invalid={errors.password ? 'true' : undefined}
                  aria-required='true'
                  disabled={isSubmitting}
                />
                <button
                  type='button'
                  className='field__password-toggle'
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={0}
                >
                  {showPassword ? '🙈' : '👁'}
                </button>
              </div>
              {errors.password && (
                <p className='field__error' id={passwordErrId} role='alert'>
                  {errors.password}
                </p>
              )}
              {values.password.length > 0 && (
                <div className='strength-meter' id={`${baseId}-strength`} aria-live='polite'>
                  <div className='strength-meter__bars' aria-hidden='true'>
                    {[0, 1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className='strength-meter__bar'
                        style={{
                          background:
                            i < passwordStrength.score
                              ? strengthColors[passwordStrength.score - 1]
                              : undefined,
                        }}
                      />
                    ))}
                  </div>
                  <span className='strength-meter__label'>
                    {passwordStrength.score > 0
                      ? strengthLabels[passwordStrength.score - 1]
                      : 'Very weak'}
                  </span>
                  <div className='strength-meter__checks'>
                    {[
                      { label: '8+ characters', pass: values.password.length >= 8 },
                      { label: 'Uppercase', pass: /[A-Z]/.test(values.password) },
                      { label: 'Lowercase', pass: /[a-z]/.test(values.password) },
                      { label: 'Number', pass: /\d/.test(values.password) },
                    ].map(({ label, pass }) => (
                      <span
                        key={label}
                        className={`strength-meter__check${pass ? ' strength-meter__check--pass' : ''}`}
                      >
                        <span aria-hidden='true'>{pass ? '✓' : '○'}</span>
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div className={`auth-card__field${errors.confirmPassword ? ' field--error' : ''}`}>
              <label htmlFor={confirmPasswordId}>Confirm password</label>
              <div className='field__password-wrapper'>
                <input
                  id={confirmPasswordId}
                  name='confirmPassword'
                  type={showConfirm ? 'text' : 'password'}
                  autoComplete='new-password'
                  value={values.confirmPassword}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  aria-describedby={errors.confirmPassword ? confirmPasswordErrId : undefined}
                  aria-invalid={errors.confirmPassword ? 'true' : undefined}
                  aria-required='true'
                  disabled={isSubmitting}
                />
                <button
                  type='button'
                  className='field__password-toggle'
                  aria-label={showConfirm ? 'Hide confirm password' : 'Show confirm password'}
                  onClick={() => setShowConfirm((v) => !v)}
                  tabIndex={0}
                >
                  {showConfirm ? '🙈' : '👁'}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className='field__error' id={confirmPasswordErrId} role='alert'>
                  {errors.confirmPassword}
                </p>
              )}
            </div>

            {/* Accept Terms */}
            <div
              className={`auth-card__field auth-card__field--checkbox${errors.acceptTerms ? ' field--error' : ''}`}
            >
              <input
                id={acceptTermsId}
                name='acceptTerms'
                type='checkbox'
                checked={values.acceptTerms}
                onChange={handleChange}
                onBlur={handleBlur}
                aria-describedby={errors.acceptTerms ? acceptTermsErrId : undefined}
                aria-invalid={errors.acceptTerms ? 'true' : undefined}
                aria-required='true'
                disabled={isSubmitting}
              />
              <label htmlFor={acceptTermsId}>
                I agree to the{' '}
                <a className='link' href='/terms' target='_blank' rel='noopener noreferrer'>
                  Terms of Service
                </a>{' '}
                and{' '}
                <a className='link' href='/privacy' target='_blank' rel='noopener noreferrer'>
                  Privacy Policy
                </a>
              </label>
              {errors.acceptTerms && (
                <p className='field__error' id={acceptTermsErrId} role='alert'>
                  {errors.acceptTerms}
                </p>
              )}
            </div>

            <button
              type='submit'
              className='auth-card__submit'
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting && <span className='spinner' aria-hidden='true' />}
              {isSubmitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className='auth-card__footer'>
            Already have an account?{' '}
            <Link className='link' to='/login'>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  );
};

export default RegisterPage;
