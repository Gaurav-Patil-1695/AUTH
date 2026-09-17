import React from 'react';

interface TextFieldProps {
  id: string;
  label: string;
  type?: 'text' | 'email';
  value: string;
  onChange: (value: string) => void;
  error?: string;
  hint?: string;
  autoComplete?: string;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
}

function TextField({
  id,
  label,
  type = 'text',
  value,
  onChange,
  error,
  hint,
  autoComplete,
  disabled = false,
  required = false,
  placeholder,
}: TextFieldProps): JSX.Element {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;

  const describedBy: string[] = [];
  if (hint) describedBy.push(hintId);
  if (error) describedBy.push(errorId);

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
      <input
        id={id}
        type={type}
        className="field__input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        disabled={disabled}
        required={required}
        placeholder={placeholder}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy.length > 0 ? describedBy.join(' ') : undefined}
      />
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

export default TextField;
