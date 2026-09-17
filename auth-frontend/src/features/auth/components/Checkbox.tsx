import React from 'react';

interface CheckboxProps {
  id: string;
  label: React.ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

function Checkbox({
  id,
  label,
  checked,
  onChange,
  error,
  disabled = false,
  required = false,
}: CheckboxProps): JSX.Element {
  const errorId = `${id}-error`;

  return (
    <div className={`checkbox${error ? ' checkbox--error' : ''}`}>
      <label className="checkbox__label" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          className="checkbox__input"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          required={required}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? errorId : undefined}
        />
        <span className="checkbox__control" aria-hidden="true" />
        <span className="checkbox__text">{label}</span>
      </label>
      {error && (
        <span id={errorId} className="checkbox__error field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export default Checkbox;
