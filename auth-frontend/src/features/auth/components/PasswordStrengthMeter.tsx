import React from 'react';

interface Rule {
  key: string;
  label: string;
  test: (password: string) => boolean;
}

const RULES: Rule[] = [
  {
    key: 'length',
    label: 'At least 8 characters',
    test: (p) => p.length >= 8,
  },
  {
    key: 'uppercase',
    label: 'At least one uppercase letter',
    test: (p) => /[A-Z]/.test(p),
  },
  {
    key: 'lowercase',
    label: 'At least one lowercase letter',
    test: (p) => /[a-z]/.test(p),
  },
  {
    key: 'number',
    label: 'At least one number',
    test: (p) => /[0-9]/.test(p),
  },
];

interface PasswordStrengthMeterProps {
  password: string;
}

function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps): JSX.Element {
  const results = RULES.map((rule) => ({
    key: rule.key,
    label: rule.label,
    passed: rule.test(password),
  }));

  const passedCount = results.filter((r) => r.passed).length;

  function getStrengthLabel(): string {
    if (password.length === 0) return '';
    if (passedCount <= 1) return 'Weak';
    if (passedCount === 2) return 'Fair';
    if (passedCount === 3) return 'Good';
    return 'Strong';
  }

  function getStrengthModifier(): string {
    if (password.length === 0) return '';
    if (passedCount <= 1) return 'strength-meter--weak';
    if (passedCount === 2) return 'strength-meter--fair';
    if (passedCount === 3) return 'strength-meter--good';
    return 'strength-meter--strong';
  }

  const strengthLabel = getStrengthLabel();
  const strengthModifier = getStrengthModifier();

  return (
    <div className={`strength-meter${strengthModifier ? ` ${strengthModifier}` : ''}`} aria-label="Password strength">
      <div className="strength-meter__bar-row" aria-hidden="true">
        {RULES.map((rule, index) => (
          <div
            key={rule.key}
            className={`strength-meter__segment${
              password.length > 0 && index < passedCount
                ? ' strength-meter__segment--filled'
                : ''
            }`}
          />
        ))}
      </div>
      {strengthLabel && (
        <span className="strength-meter__label" aria-live="polite">
          {strengthLabel}
        </span>
      )}
      <ul className="strength-meter__checklist" aria-label="Password requirements">
        {results.map((result) => (
          <li
            key={result.key}
            className={`strength-meter__rule${
              result.passed ? ' strength-meter__rule--passed' : ''
            }`}
          >
            <span
              className="strength-meter__rule-icon"
              aria-hidden="true"
            >
              {result.passed ? '\u2713' : '\u25CB'}
            </span>
            <span className="strength-meter__rule-text">{result.label}</span>
            <span className="sr-only">
              {result.passed ? 'passed' : 'not met'}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PasswordStrengthMeter;
