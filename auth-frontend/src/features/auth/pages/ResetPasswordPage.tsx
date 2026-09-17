import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../../../api/auth';

const passwordRules = {
  minLength: (v: string) => v.length >= 8,
  hasUppercase: (v: string) => /[A-Z]/.test(v),
  hasLowercase: (v: string) => /[a-z]/.test(v),
  hasNumber: (v: string) => /[0-9]/.test(v),
};

function getPasswordStrength(password: string): number {
  return [
    passwordRules.minLength(password),
    passwordRules.hasUppercase(password),
    passwordRules.hasLowercase(password),
    passwordRules.hasNumber(password),
  ].filter(Boolean).length;
}

const styles = `
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
    --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-input: 8px;
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 48px;
  }

  .reset-password-app {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--family-base);
    color: var(--color-text-primary);
    padding: var(--space-md);
  }

  .reset-password-app__branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .reset-password-app__brand-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--color-accent-primary);
    letter-spacing: -0.01em;
  }

  .auth-card {
    background: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 400px;
  }

  .auth-card__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-sm) 0;
  }

  .auth-card__subtitle {
    font-size: 14px;
    font-weight: 400;
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

  .auth-card__label {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  .auth-card__input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .auth-card__input {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    padding-right: 44px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    font-size: 16px;
    font-family: var(--family-base);
    color: var(--color-text-primary);
    background: var(--color-surface);
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    box-sizing: border-box;
  }

  .auth-card__input:focus {
    border-color: var(--color-accent-primary);
    box-shadow: var(--elevation-focus);
  }

  .auth-card__input.field--error {
    border-color: var(--color-error);
  }

  .auth-card__input.field--error:focus {
    box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
  }

  .auth-card__toggle {
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
    border-radius: var(--radius-button);
  }

  .auth-card__toggle:focus-visible {
    outline: 2px solid var(--color-focus-ring);
    outline-offset: 2px;
  }

  .auth-card__field-error {
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-error);
  }

  .auth-card__strength {
    margin-top: var(--space-xs);
  }

  .auth-card__strength-bars {
    display: flex;
    gap: var(--space-xs);
    margin-bottom: var(--space-xs);
  }

  .strength-bar {
    height: 4px;
    flex: 1;
    border-radius: 9999px;
    background: var(--color-border);
    transition: background 0.2s;
  }

  .strength-bar--1 { background: var(--color-error); }
  .strength-bar--2 { background: var(--color-warning); }
  .strength-bar--3 { background: var(--color-info); }
  .strength-bar--4 { background: var(--color-success); }

  .auth-card__strength-label {
    font-size: 12px;
    color: var(--color-text-muted);
  }

  .auth-card__submit {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    background: var(--color-accent-primary);
    color: #fff;
    border: none;
    border-radius: var(--radius-button);
    font-size: 16px;
    font-weight: 600;
    font-family: var(--family-base);
    cursor: pointer;
    transition: background 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    margin-top: var(--space-sm);
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
    outline: 2px solid var(--color-focus-ring);
    outline-offset: 2px;
  }

  .auth-card__banner {
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: var(--space-md);
  }

  .auth-card__banner--error {
    background: #fef2f2;
    color: var(--color-error);
    border: 1px solid #fecaca;
  }

  .auth-card__banner--success {
    background: #f0fdf4;
    color: var(--color-success);
    border: 1px solid #bbf7d0;
  }

  .auth-card__back-link {
    display: block;
    text-align: center;
    margin-top: var(--space-lg);
    font-size: 14px;
    color: var(--color-link);
    text-decoration: none;
    font-weight: 500;
  }

  .auth-card__back-link:hover {
    text-decoration: underline;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

interface FormState {
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  password?: string;
  confirmPassword?: string;
}

function validate(values: FormState): FormErrors {
  const errors: FormErrors = {};

  if (!values.password) {
    errors.password = 'Password is required.';
  } else if (values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/[A-Z]/.test(values.password)) {
    errors.password = 'Password must contain at least one uppercase letter.';
  } else if (!/[a-z]/.test(values.password)) {
    errors.password = 'Password must contain at least one lowercase letter.';
  } else if (!/[0-9]/.test(values.password)) {
    errors.password = 'Password must contain at least one number.';
  }

  if (!values.confirmPassword) {
    errors.confirmPassword = 'Please confirm your password.';
  } else if (values.password !== values.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  return errors;
}

const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];

const EyeIcon: React.FC<{ visible: boolean }> = ({ visible }) =>
  visible ? (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  ) : (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';

  const [values, setValues] = useState<FormState>({ password: '', confirmPassword: '' });
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bannerError, setBannerError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);
    return () => { document.head.removeChild(styleEl); };
  }, []);

  const handleChange = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const next = { ...values, [field]: e.target.value };
    setValues(next);
    if (touched[field]) {
      setErrors(validate(next));
    }
  };

  const handleBlur = (field: keyof FormState) => () => {
    setTouched(prev => ({ ...prev, [field]: true }));
    setErrors(validate(values));
  };

  const strength = getPasswordStrength(values.password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ password: true, confirmPassword: true });
    const errs = validate(values);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    if (!token) {
      setBannerError('Reset token is missing or invalid. Please request a new password reset link.');
      return;
    }

    setIsSubmitting(true);
    setBannerError('');

    try {
      await resetPassword({ token, password: values.password, confirmPassword: values.confirmPassword });
      setIsSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { error?: { message?: string } } } };
        const message = axiosErr.response?.data?.error?.message;
        setBannerError(message ?? 'An error occurred. Please try again.');
      } else {
        setBannerError('An error occurred. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="reset-password-app">
      <div className="reset-password-app__branding" aria-label="Application branding">
        <span className="reset-password-app__brand-name">auth-starter</span>
      </div>

      <div className="auth-card" role="main">
        <h1 className="auth-card__title">Set new password</h1>
        <p className="auth-card__subtitle">
          Choose a strong password for your account.
        </p>

        <div aria-live="polite" aria-atomic="true">
          {bannerError && (
            <div className="auth-card__banner auth-card__banner--error" role="alert">
              {bannerError}
            </div>
          )}
          {isSuccess && (
            <div className="auth-card__banner auth-card__banner--success" role="status">
              Your password has been reset successfully. Redirecting to login…
            </div>
          )}
        </div>

        {!isSuccess && (
          <form className="auth-card__form" onSubmit={handleSubmit} noValidate>
            <div className="auth-card__field">
              <label className="auth-card__label" htmlFor="password">
                New Password
              </label>
              <div className="auth-card__input-wrapper">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  className={`auth-card__input${errors.password && touched.password ? ' field--error' : ''}`}
                  value={values.password}
                  onChange={handleChange('password')}
                  onBlur={handleBlur('password')}
                  autoComplete="new-password"
                  aria-describedby={errors.password && touched.password ? 'password-error' : 'password-strength'}
                  aria-invalid={!!(errors.password && touched.password)}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="auth-card__toggle"
                  onClick={() => setShowPassword(prev => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={0}
                >
                  <EyeIcon visible={showPassword} />
                </button>
              </div>
              {errors.password && touched.password ? (
                <span id="password-error" className="auth-card__field-error" role="alert">
                  {errors.password}
                </span>
              ) : (
                values.password && (
                  <div id="password-strength" className="auth-card__strength">
                    <div className="auth-card__strength-bars" aria-hidden="true">
                      {[1, 2, 3, 4].map(level => (
                        <div
                          key={level}
                          className={`strength-bar${strength >= level ? ` strength-bar--${strength}` : ''}`}
                        />
                      ))}
                    </div>
                    <span className="auth-card__strength-label">
                      Password strength: {strengthLabels[strength] ?? ''}
                    </span>
                  </div>
                )
              )}
            </div>

            <div className="auth-card__field">
              <label className="auth-card__label" htmlFor="confirmPassword">
                Confirm Password
              </label>
              <div className="auth-card__input-wrapper">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirm ? 'text' : 'password'}
                  className={`auth-card__input${errors.confirmPassword && touched.confirmPassword ? ' field--error' : ''}`}
                  value={values.confirmPassword}
                  onChange={handleChange('confirmPassword')}
                  onBlur={handleBlur('confirmPassword')}
                  autoComplete="new-password"
                  aria-describedby={errors.confirmPassword && touched.confirmPassword ? 'confirmPassword-error' : undefined}
                  aria-invalid={!!(errors.confirmPassword && touched.confirmPassword)}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="auth-card__toggle"
                  onClick={() => setShowConfirm(prev => !prev)}
                  aria-label={showConfirm ? 'Hide confirm password' : 'Show confirm password'}
                  tabIndex={0}
                >
                  <EyeIcon visible={showConfirm} />
                </button>
              </div>
              {errors.confirmPassword && touched.confirmPassword && (
                <span id="confirmPassword-error" className="auth-card__field-error" role="alert">
                  {errors.confirmPassword}
                </span>
              )}
            </div>

            <button
              type="submit"
              className="auth-card__submit"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Resetting…
                </>
              ) : (
                'Reset Password'
              )}
            </button>
          </form>
        )}

        <a href="/login" className="auth-card__back-link">
          Back to Sign in
        </a>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
