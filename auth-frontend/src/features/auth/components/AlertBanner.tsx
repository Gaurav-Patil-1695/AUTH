import React from 'react';

interface AlertBannerProps {
  type: 'success' | 'error';
  message: string;
}

function AlertBanner({ type, message }: AlertBannerProps): JSX.Element {
  return (
    <div
      className={`alert-banner alert-banner--${type}`}
      aria-live="polite"
      aria-atomic="true"
      role={type === 'error' ? 'alert' : 'status'}
    >
      <span className="alert-banner__icon" aria-hidden="true">
        {type === 'success' ? (
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            focusable="false"
          >
            <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M5.5 9L7.5 11L12.5 6.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ) : (
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            focusable="false"
          >
            <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M9 5.5V9.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <circle cx="9" cy="12" r="0.75" fill="currentColor" />
          </svg>
        )}
      </span>
      <span className="alert-banner__message">{message}</span>
    </div>
  );
}

export default AlertBanner;
