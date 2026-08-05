import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../../api/auth';

interface LoginFormState {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface LoginFormErrors {
  email?: string;
  password?: string;
  form?: string;
}

function validateLoginForm(values: LoginFormState): LoginFormErrors {
  const errors: LoginFormErrors = {};

  if (!values.email || values.email.trim() === '') {
    errors.email = 'Enter a valid email address.';
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(values.email.trim())) {
      errors.email = 'Enter a valid email address.';
    }
  }

  if (!values.password || values.password.length < 1) {
    errors.password = 'Password is required.';
  }

  return errors;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const [formValues, setFormValues] = useState<LoginFormState>({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormValues((prev) => ({ ...prev, email: e.target.value }));
    if (errors.email) {
      setErrors((prev) => ({ ...prev, email: undefined }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormValues((prev) => ({ ...prev, password: e.target.value }));
    if (errors.password) {
      setErrors((prev) => ({ ...prev, password: undefined }));
    }
  };

  const handleRememberMeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormValues((prev) => ({ ...prev, rememberMe: e.target.checked }));
  };

  const handleTogglePassword = () => {
    setShowPassword((prev) => !prev);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const validationErrors = validateLoginForm(formValues);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      await login({
        email: formValues.email.trim(),
        password: formValues.password,
        rememberMe: formValues.rememberMe,
      });
      navigate('/');
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Invalid email or password.';
      setErrors({ form: message });
    } finally {
      setIsSubmitting(false);
    }
  };

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

        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }

        body {
          font-family: var(--family-base);
          background-color: var(--color-bg-app);
          color: var(--color-text-primary);
          font-size: 16px;
          line-height: 1.5;
        }

        .login-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background-color: var(--color-bg-app);
          padding: var(--space-lg);
        }

        .login-page__branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .login-page__brand-name {
          font-size: 18px;
          font-weight: 600;
          line-height: 1.25;
          color: var(--color-accent-primary);
          font-family: var(--family-base);
        }

        .auth-card {
          background-color: var(--color-surface);
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
          margin-bottom: var(--space-sm);
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-xl);
        }

        .auth-card__fields {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
          margin-bottom: var(--space-lg);
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

        .auth-card__field .field__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .auth-card__field input[type='email'],
        .auth-card__field input[type='password'],
        .auth-card__field input[type='text'] {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-size: 16px;
          font-family: var(--family-base);
          line-height: 1.5;
          color: var(--color-text-primary);
          background-color: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .auth-card__field input[type='email']:focus,
        .auth-card__field input[type='password']:focus,
        .auth-card__field input[type='text']:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .auth-card__field input.field--error {
          border-color: var(--color-error);
        }

        .auth-card__field input.field--error:focus {
          box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
        }

        .auth-card__field input[type='password'],
        .auth-card__field input[type='text'] {
          padding-right: 44px;
        }

        .field__toggle-password {
          position: absolute;
          right: var(--space-sm);
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--space-xs);
          color: var(--color-text-muted);
          font-size: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-sm);
          transition: color 0.15s;
        }

        .field__toggle-password:hover {
          color: var(--color-text-secondary);
        }

        .field__toggle-password:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .field__error {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
        }

        .auth-card__row--remember-forgot {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-lg);
          flex-wrap: wrap;
          gap: var(--space-sm);
        }

        .auth-card__remember {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
        }

        .auth-card__remember input[type='checkbox'] {
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
          border-radius: var(--radius-sm);
        }

        .auth-card__remember label {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          cursor: pointer;
        }

        .link {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-link);
          text-decoration: none;
          transition: color 0.15s;
        }

        .link:hover {
          color: var(--color-accent-primary-hover);
          text-decoration: underline;
        }

        .link:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
          border-radius: var(--radius-sm);
        }

        .btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          width: 100%;
          padding: var(--space-sm) var(--space-lg);
          font-size: 16px;
          font-weight: 600;
          font-family: var(--family-base);
          line-height: 1.5;
          border-radius: var(--radius-button);
          border: none;
          cursor: pointer;
          transition: background-color 0.15s, box-shadow 0.15s;
          text-decoration: none;
        }

        .btn--primary {
          background-color: var(--color-accent-primary);
          color: var(--color-surface);
        }

        .btn--primary:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .btn--primary:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .btn--primary:focus-visible {
          outline: none;
          box-shadow: var(--elevation-focus);
        }

        .btn--primary:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .btn__spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #ffffff;
          border-radius: var(--radius-full);
          animation: spin 0.7s linear infinite;
          flex-shrink: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card__form-error {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-error);
          background-color: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          margin-bottom: var(--space-md);
        }

        .auth-card__footer {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          text-align: center;
          margin-top: var(--space-lg);
        }

        .auth-card__footer .link {
          margin-left: var(--space-xs);
        }
      `}</style>

      <main className='login-page'>
        <div className='login-page__branding' aria-label='auth-starter'>
          <span className='login-page__brand-name'>auth-starter</span>
        </div>

        <form
          className='auth-card'
          aria-labelledby='login-title'
          noValidate
          onSubmit={handleSubmit}
        >
          <h1 className='auth-card__title' id='login-title'>
            Sign in
          </h1>
          <p className='auth-card__subtitle'>Welcome back. Sign in to your account.</p>

          {errors.form && (
            <div
              className='auth-card__form-error'
              role='alert'
              aria-live='polite'
            >
              {errors.form}
            </div>
          )}

          <div className='auth-card__fields'>
            <div className='auth-card__field'>
              <label htmlFor='login-email'>Email address</label>
              <div className='field__input-wrapper'>
                <input
                  id='login-email'
                  type='email'
                  name='email'
                  autoComplete='email'
                  value={formValues.email}
                  onChange={handleEmailChange}
                  className={errors.email ? 'field--error' : ''}
                  aria-describedby={errors.email ? 'login-email-error' : undefined}
                  aria-invalid={errors.email ? true : undefined}
                  disabled={isSubmitting}
                  required
                />
              </div>
              {errors.email && (
                <span
                  id='login-email-error'
                  className='field__error'
                  role='alert'
                >
                  {errors.email}
                </span>
              )}
            </div>

            <div className='auth-card__field'>
              <label htmlFor='login-password'>Password</label>
              <div className='field__input-wrapper'>
                <input
                  id='login-password'
                  type={showPassword ? 'text' : 'password'}
                  name='password'
                  autoComplete='current-password'
                  value={formValues.password}
                  onChange={handlePasswordChange}
                  className={errors.password ? 'field--error' : ''}
                  aria-describedby={errors.password ? 'login-password-error' : undefined}
                  aria-invalid={errors.password ? true : undefined}
                  disabled={isSubmitting}
                  required
                />
                <button
                  type='button'
                  className='field__toggle-password'
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={handleTogglePassword}
                  tabIndex={0}
                >
                  {showPassword ? (
                    <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round' aria-hidden='true'>
                      <path d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94'/>
                      <path d='M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19'/>
                      <line x1='1' y1='1' x2='23' y2='23'/>
                    </svg>
                  ) : (
                    <svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round' aria-hidden='true'>
                      <path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'/>
                      <circle cx='12' cy='12' r='3'/>
                    </svg>
                  )}
                </button>
              </div>
              {errors.password && (
                <span
                  id='login-password-error'
                  className='field__error'
                  role='alert'
                >
                  {errors.password}
                </span>
              )}
            </div>
          </div>

          <div className='auth-card__row--remember-forgot'>
            <div className='auth-card__remember'>
              <input
                id='login-remember-me'
                type='checkbox'
                name='rememberMe'
                checked={formValues.rememberMe}
                onChange={handleRememberMeChange}
                disabled={isSubmitting}
              />
              <label htmlFor='login-remember-me'>Remember me</label>
            </div>
            <Link to='/forgot-password' className='link'>
              Forgot password?
            </Link>
          </div>

          <button
            type='submit'
            className='btn btn--primary'
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className='btn__spinner' aria-hidden='true' />}
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className='auth-card__footer'>
            Don&rsquo;t have an account?
            <Link to='/register' className='link'>
              Create account
            </Link>
          </p>
        </form>
      </main>
    </>
  );
};

export default LoginPage;
