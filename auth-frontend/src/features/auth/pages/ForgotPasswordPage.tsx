import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../../../api/auth';

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
    --space-2xl: 48px;
    --space-lg: 24px;
    --space-md: 16px;
    --space-sm: 8px;
    --space-xl: 32px;
    --space-xs: 4px;
  }

  .forgot-page {
    min-height: 100vh;
    background: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--family-base);
    padding: var(--space-md);
  }

  .forgot-page__branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .forgot-page__logo {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-accent-primary);
    letter-spacing: -0.5px;
  }

  .auth-card {
    background: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 420px;
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

  .auth-card__field {
    margin-bottom: var(--space-md);
  }

  .auth-card__label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-primary);
    margin-bottom: var(--space-xs);
  }

  .auth-card__input {
    width: 100%;
    padding: 10px var(--space-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    font-size: 16px;
    font-family: var(--family-base);
    color: var(--color-text-primary);
    background: var(--color-surface);
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }

  .auth-card__input:focus {
    border-color: var(--color-accent-primary);
    box-shadow: var(--elevation-focus);
  }

  .auth-card__input.field--error {
    border-color: var(--color-error);
  }

  .auth-card__input:disabled {
    background: var(--color-muted-surface);
    color: var(--color-text-muted);
    cursor: not-allowed;
  }

  .auth-card__field-error {
    font-size: 12px;
    color: var(--color-error);
    margin-top: var(--space-xs);
    line-height: 1.5;
  }

  .auth-card__submit {
    width: 100%;
    padding: 10px var(--space-md);
    background: var(--color-accent-primary);
    color: var(--color-surface);
    border: none;
    border-radius: var(--radius-button);
    font-size: 16px;
    font-weight: 600;
    font-family: var(--family-base);
    cursor: pointer;
    margin-top: var(--space-sm);
    transition: background 0.15s;
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

  .auth-card__spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    flex-shrink: 0;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
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

  .auth-card__footer {
    text-align: center;
    margin-top: var(--space-lg);
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .auth-card__link {
    color: var(--color-link);
    text-decoration: none;
    font-weight: 500;
  }

  .auth-card__link:hover {
    text-decoration: underline;
  }
`;

function injectStyles(id: string, css: string): void {
  if (typeof document !== 'undefined' && !document.getElementById(id)) {
    const tag = document.createElement('style');
    tag.id = id;
    tag.textContent = css;
    document.head.appendChild(tag);
  }
}

const EMAIL_REQUIRED = 'Email is required.';
const EMAIL_INVALID = 'Enter a valid email address.';

function validateEmail(value: string): string {
  if (!value.trim()) return EMAIL_REQUIRED;
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(value.trim())) return EMAIL_INVALID;
  return '';
}

const ForgotPasswordPage: React.FC = () => {
  injectStyles('forgot-password-styles', styles);

  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bannerError, setBannerError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setEmail(e.target.value);
    if (emailError) {
      setEmailError(validateEmail(e.target.value));
    }
  };

  const handleEmailBlur = (): void => {
    setEmailError(validateEmail(email));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setBannerError('');

    const err = validateEmail(email);
    if (err) {
      setEmailError(err);
      return;
    }

    setIsSubmitting(true);
    try {
      await forgotPassword({ email: email.trim() });
      setSuccess(true);
    } catch {
      setBannerError('Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className='forgot-page'>
      <div className='forgot-page__branding'>
        <span className='forgot-page__logo'>auth-starter</span>
      </div>

      <div className='auth-card'>
        <h1 className='auth-card__title'>Forgot password</h1>
        <p className='auth-card__subtitle'>
          Enter your email address and we&rsquo;ll send you a link to reset your password.
        </p>

        <div aria-live='polite'>
          {bannerError && !success && (
            <div className='auth-card__banner auth-card__banner--error' role='alert'>
              {bannerError}
            </div>
          )}
          {success && (
            <div className='auth-card__banner auth-card__banner--success' role='status'>
              If an account with that email exists, you will receive a password reset link shortly.
            </div>
          )}
        </div>

        {!success && (
          <form onSubmit={handleSubmit} noValidate>
            <div className='auth-card__field'>
              <label className='auth-card__label' htmlFor='email'>
                Email address
              </label>
              <input
                id='email'
                type='email'
                className={`auth-card__input${emailError ? ' field--error' : ''}`}
                value={email}
                onChange={handleEmailChange}
                onBlur={handleEmailBlur}
                autoComplete='email'
                disabled={isSubmitting}
                aria-describedby={emailError ? 'email-error' : undefined}
                aria-invalid={emailError ? 'true' : 'false'}
              />
              {emailError && (
                <span id='email-error' className='auth-card__field-error' role='alert'>
                  {emailError}
                </span>
              )}
            </div>

            <button
              type='submit'
              className='auth-card__submit'
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting && <span className='auth-card__spinner' aria-hidden='true' />}
              {isSubmitting ? 'Sending…' : 'Send reset link'}
            </button>
          </form>
        )}

        <div className='auth-card__footer'>
          Remember your password?{' '}
          <Link to='/login' className='auth-card__link'>
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
