import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../features/auth/context/AuthContext';
import { logout } from '../api/auth';

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

  .profile-page {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-lg);
    font-family: var(--family-base);
  }

  .profile-branding {
    text-align: center;
    margin-bottom: var(--space-lg);
  }

  .profile-branding__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-accent-primary);
    margin: 0 0 var(--space-xs) 0;
  }

  .profile-branding__subtitle {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0;
  }

  .profile-card {
    background-color: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 480px;
  }

  .profile-card__heading {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-xs) 0;
  }

  .profile-card__subheading {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-xl) 0;
  }

  .profile-card__avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 72px;
    height: 72px;
    border-radius: var(--radius-full);
    background-color: var(--color-accent-primary);
    color: var(--color-surface);
    font-size: 28px;
    font-weight: 700;
    margin: 0 auto var(--space-lg) auto;
    line-height: 1;
  }

  .profile-card__fields {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
    margin-bottom: var(--space-xl);
  }

  .profile-card__field {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .profile-card__label {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
  }

  .profile-card__value {
    font-size: 16px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-primary);
    background-color: var(--color-muted-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
  }

  .profile-card__badge {
    display: inline-block;
    font-size: 12px;
    font-weight: 500;
    line-height: 1.5;
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-full);
  }

  .profile-card__badge--active {
    background-color: #dcfce7;
    color: var(--color-success);
  }

  .profile-card__badge--inactive {
    background-color: #fee2e2;
    color: var(--color-error);
  }

  .profile-card__divider {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: 0 0 var(--space-xl) 0;
  }

  .profile-card__actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    font-family: var(--family-base);
    font-size: 16px;
    font-weight: 500;
    line-height: 1.5;
    border-radius: var(--radius-button);
    padding: var(--space-sm) var(--space-lg);
    cursor: pointer;
    border: none;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
    width: 100%;
  }

  .btn:focus-visible {
    outline: none;
    box-shadow: var(--elevation-focus);
  }

  .btn:disabled {
    cursor: not-allowed;
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

  .btn--primary:disabled {
    background-color: var(--color-accent-disabled);
  }

  .btn--danger {
    background-color: transparent;
    color: var(--color-error);
    border: 1px solid var(--color-error);
  }

  .btn--danger:hover:not(:disabled) {
    background-color: #fee2e2;
  }

  .btn--danger:active:not(:disabled) {
    background-color: #fecaca;
  }

  .btn--danger:disabled {
    opacity: 0.5;
  }

  .btn__spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: #fff;
    border-radius: var(--radius-full);
    animation: spin 0.7s linear infinite;
  }

  .btn__spinner--danger {
    border-color: rgba(220,38,38,0.3);
    border-top-color: var(--color-error);
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .profile-card__notice {
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-text-muted);
    text-align: center;
    margin-top: var(--space-md);
  }

  .profile-banner {
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    margin-bottom: var(--space-md);
  }

  .profile-banner--error {
    background-color: #fee2e2;
    color: var(--color-error);
    border: 1px solid #fca5a5;
  }

  .profile-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background-color: var(--color-bg-app);
    font-family: var(--family-base);
    font-size: 16px;
    color: var(--color-text-secondary);
  }
`;

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  if (parts.length === 0 || parts[0] === '') return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

const ProfilePage: React.FC = () => {
  const authContext = useContext(AuthContext);
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  useEffect(() => {
    if (!authContext) return;
    if (!authContext.isLoading && !authContext.isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [authContext, navigate]);

  if (!authContext || authContext.isLoading) {
    return (
      <>
        <style>{styles}</style>
        <div className="profile-loading" role="status" aria-live="polite">
          Loading profile…
        </div>
      </>
    );
  }

  const { user } = authContext;

  if (!user) {
    return null;
  }

  const handleLogout = async () => {
    setIsLoggingOut(true);
    setLogoutError(null);
    try {
      await logout();
      authContext.logout();
      navigate('/login', { replace: true });
    } catch {
      setLogoutError('An unexpected error occurred. Please try again.');
      setIsLoggingOut(false);
    }
  };

  const initials = getInitials(user.fullName ?? user.full_name ?? '');
  const displayName = user.fullName ?? user.full_name ?? '';
  const displayEmail = user.email ?? '';
  const isActive = user.isActive ?? user.is_active ?? false;
  const createdAt = user.createdAt ?? user.created_at ?? '';

  return (
    <>
      <style>{styles}</style>
      <div className="profile-page">
        <div className="profile-branding" aria-hidden="false">
          <h1 className="profile-branding__title">auth-starter</h1>
          <p className="profile-branding__subtitle">Secure authentication made simple</p>
        </div>

        <main className="profile-card" role="main">
          <div className="profile-card__avatar" aria-hidden="true">
            {initials}
          </div>

          <h2 className="profile-card__heading">Your Profile</h2>
          <p className="profile-card__subheading">Account details and session management</p>

          {logoutError && (
            <div
              className="profile-banner profile-banner--error"
              role="alert"
              aria-live="polite"
            >
              {logoutError}
            </div>
          )}

          <dl className="profile-card__fields">
            <div className="profile-card__field">
              <dt className="profile-card__label">Full Name</dt>
              <dd className="profile-card__value">{displayName}</dd>
            </div>

            <div className="profile-card__field">
              <dt className="profile-card__label">Email Address</dt>
              <dd className="profile-card__value">{displayEmail}</dd>
            </div>

            <div className="profile-card__field">
              <dt className="profile-card__label">Account Status</dt>
              <dd className="profile-card__value" style={{ background: 'none', border: 'none', padding: 0 }}>
                <span
                  className={`profile-card__badge ${
                    isActive
                      ? 'profile-card__badge--active'
                      : 'profile-card__badge--inactive'
                  }`}
                >
                  {isActive ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>

            {createdAt && (
              <div className="profile-card__field">
                <dt className="profile-card__label">Member Since</dt>
                <dd className="profile-card__value">{formatDate(createdAt)}</dd>
              </div>
            )}
          </dl>

          <hr className="profile-card__divider" />

          <div className="profile-card__actions">
            <button
              type="button"
              className="btn btn--danger"
              onClick={handleLogout}
              disabled={isLoggingOut}
              aria-busy={isLoggingOut}
            >
              {isLoggingOut ? (
                <>
                  <span className="btn__spinner btn__spinner--danger" aria-hidden="true" />
                  Signing out…
                </>
              ) : (
                'Sign Out'
              )}
            </button>
          </div>

          <p className="profile-card__notice">
            Your session is protected with short-lived JWT access tokens.
          </p>
        </main>
      </div>
    </>
  );
};

export default ProfilePage;
