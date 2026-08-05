import React, { useState } from 'react';

interface PasswordFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  hint?: string;
  autoComplete?: string;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
}

function PasswordField({
  id,
  label,
  value,
  onChange,
  error,
  hint,
  autoComplete,
  disabled = false,
  required = false,
  placeholder,
}: PasswordFieldProps): JSX.Element {
  const [visible, setVisible] = useState(false);

  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  const describedBy: string[] = [];
  if (hint) describedBy.push(hintId);
  if (error) describedBy.push(errorId);

  function handleToggle(): void {
    setVisible((prev) => !prev);
  }

  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      <label className="field__label" htmlFor={id}>
        {label}
        {required && (
          <span className="field__required" aria-hidden="true">
            {' '}*
          </span>
        )}
      </label>
      <div className="field__input-wrapper">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          className="field__input field__input--password"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          disabled={disabled}
          required={required}
          placeholder={placeholder}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy.length > 0 ? describedBy.join(' ') : undefined}
        />
        <button
          type="button"
          className="field__toggle"
          aria-label={visible ? 'Hide password' : 'Show password'}
          onClick={handleToggle}
          disabled={disabled}
          tabIndex={0}
        >
          {visible ? (
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M2.5 10C2.5 10 5 4.5 10 4.5C15 4.5 17.5 10 17.5 10C17.5 10 15 15.5 10 15.5C5 15.5 2.5 10 2.5 10Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle
                cx="10"
                cy="10"
                r="2.5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M3 3L17 17"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M2.5 10C2.5 10 5 4.5 10 4.5C15 4.5 17.5 10 17.5 10C17.5 10 15 15.5 10 15.5C5 15.5 2.5 10 2.5 10Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle
                cx="10"
                cy="10"
                r="2.5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          )}
        </button>
      </div>
      {hint && !error && (
        <span id={hintId} className="field__hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export default PasswordField;
