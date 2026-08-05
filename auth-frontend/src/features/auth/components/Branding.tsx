import React from 'react';

function Branding(): JSX.Element {
  return (
    <div className="branding">
      <div className="branding__logo" aria-hidden="true">
        <svg
          width="48"
          height="48"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="branding__logo-icon"
        >
          <rect width="48" height="48" rx="12" fill="var(--color-accent-primary)" />
          <path
            d="M24 12C18.477 12 14 16.477 14 22C14 25.18 15.47 28.02 17.76 29.9C16.67 30.47 15.75 31.33 15.12 32.4C14.4 33.6 14 35 14 36.5V37H34V36.5C34 35 33.6 33.6 32.88 32.4C32.25 31.33 31.33 30.47 30.24 29.9C32.53 28.02 34 25.18 34 22C34 16.477 29.523 12 24 12Z"
            fill="white"
          />
        </svg>
      </div>
      <div className="branding__wordmark">
        <span className="branding__wordmark-text">AuthStarter</span>
      </div>
    </div>
  );
}

export default Branding;
