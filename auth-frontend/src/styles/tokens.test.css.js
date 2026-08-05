/**
 * Unit tests for tokens.css and auth.css
 *
 * Strategy: inject the CSS files into a jsdom document via <style> tags,
 * then assert computed styles and CSS custom property values.
 *
 * Test runner: Jest (most common for React/frontend projects without explicit config)
 * Environment: jsdom (Jest default)
 */

'use strict';

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function readCss(relativePath) {
  return fs.readFileSync(path.resolve(__dirname, relativePath), 'utf8');
}

function injectStyles(cssText) {
  const style = document.createElement('style');
  style.textContent = cssText;
  document.head.appendChild(style);
  return style;
}

function cleanup(styleEl) {
  if (styleEl && styleEl.parentNode) styleEl.parentNode.removeChild(styleEl);
}

// ---------------------------------------------------------------------------
// Load CSS source text once
// ---------------------------------------------------------------------------

const tokensCss = readCss('tokens.css');
const authCss = readCss('auth.css');

// ---------------------------------------------------------------------------
// tokens.css — verify every custom property is declared
// ---------------------------------------------------------------------------

describe('tokens.css — CSS custom properties are declared', () => {
  let styleEl;

  beforeEach(() => {
    styleEl = injectStyles(tokensCss);
  });

  afterEach(() => {
    cleanup(styleEl);
  });

  // jsdom does not compute custom properties via getComputedStyle,
  // so we parse the raw CSS text and verify all expected tokens are present.

  const expectedTokens = [
    // Brand
    '--color-accent-primary',
    '--color-accent-primary-hover',
    '--color-accent-primary-active',
    // Neutral
    '--color-bg-page',
    '--color-bg-card',
    '--color-bg-input',
    '--color-bg-input-disabled',
    '--color-border-default',
    '--color-border-focus',
    '--color-border-error',
    '--color-text-primary',
    '--color-text-secondary',
    '--color-text-placeholder',
    '--color-text-disabled',
    '--color-text-inverse',
    '--color-text-link',
    '--color-text-link-hover',
    // Semantic
    '--color-error',
    '--color-error-bg',
    '--color-error-border',
    '--color-success',
    '--color-success-bg',
    '--color-success-border',
    '--color-warning',
    '--color-warning-bg',
    '--color-warning-border',
    '--color-info',
    '--color-info-bg',
    '--color-info-border',
    // Password strength
    '--color-strength-weak',
    '--color-strength-fair',
    '--color-strength-good',
    '--color-strength-strong',
    '--color-strength-empty',
    // Spacing
    '--spacing-0',
    '--spacing-1',
    '--spacing-2',
    '--spacing-3',
    '--spacing-4',
    '--spacing-5',
    '--spacing-6',
    '--spacing-8',
    '--spacing-10',
    '--spacing-12',
    '--spacing-16',
    // Border radius
    '--radius-sm',
    '--radius-md',
    '--radius-lg',
    '--radius-xl',
    '--radius-full',
    // Border width
    '--border-width-default',
    '--border-width-focus',
    // Typography — font family
    '--font-family-sans',
    '--font-family-mono',
    // Typography — font size
    '--font-size-xs',
    '--font-size-sm',
    '--font-size-md',
    '--font-size-lg',
    '--font-size-xl',
    '--font-size-2xl',
    '--font-size-3xl',
    // Typography — font weight
    '--font-weight-normal',
    '--font-weight-medium',
    '--font-weight-semibold',
    '--font-weight-bold',
    // Typography — line height
    '--line-height-tight',
    '--line-height-snug',
    '--line-height-normal',
    '--line-height-relaxed',
    // Shadow
    '--shadow-sm',
    '--shadow-md',
    '--shadow-lg',
    '--shadow-card',
    // Layout — card
    '--card-width',
    '--card-padding',
    '--card-gap',
    '--card-border-radius',
    // Layout — form
    '--form-field-gap',
    '--input-height',
    '--input-padding-x',
    '--input-padding-y',
    '--input-border-radius',
    // Transitions
    '--transition-fast',
    '--transition-base',
    '--transition-slow',
    // Z-index
    '--z-index-base',
    '--z-index-dropdown',
    '--z-index-overlay',
    '--z-index-modal',
    '--z-index-toast',
    // Branding
    '--branding-logo-size',
    '--branding-gap',
  ];

  test.each(expectedTokens)('declares %s', (token) => {
    expect(tokensCss).toContain(token);
  });
});

// ---------------------------------------------------------------------------
// tokens.css — spot-check specific values
// ---------------------------------------------------------------------------

describe('tokens.css — token values', () => {
  test('--color-accent-primary is #4f46e5', () => {
    expect(tokensCss).toMatch(/--color-accent-primary\s*:\s*#4f46e5/);
  });

  test('--color-accent-primary-hover is #4338ca', () => {
    expect(tokensCss).toMatch(/--color-accent-primary-hover\s*:\s*#4338ca/);
  });

  test('--color-accent-primary-active is #3730a3', () => {
    expect(tokensCss).toMatch(/--color-accent-primary-active\s*:\s*#3730a3/);
  });

  test('--color-error is #dc2626', () => {
    expect(tokensCss).toMatch(/--color-error\s*:\s*#dc2626/);
  });

  test('--color-success is #16a34a', () => {
    expect(tokensCss).toMatch(/--color-success\s*:\s*#16a34a/);
  });

  test('--color-warning is #d97706', () => {
    expect(tokensCss).toMatch(/--color-warning\s*:\s*#d97706/);
  });

  test('--color-info is #2563eb', () => {
    expect(tokensCss).toMatch(/--color-info\s*:\s*#2563eb/);
  });

  test('--spacing-4 is 16px', () => {
    expect(tokensCss).toMatch(/--spacing-4\s*:\s*16px/);
  });

  test('--spacing-8 is 32px', () => {
    expect(tokensCss).toMatch(/--spacing-8\s*:\s*32px/);
  });

  test('--radius-full is 9999px', () => {
    expect(tokensCss).toMatch(/--radius-full\s*:\s*9999px/);
  });

  test('--font-size-md is 1rem', () => {
    expect(tokensCss).toMatch(/--font-size-md\s*:\s*1rem/);
  });

  test('--font-weight-bold is 700', () => {
    expect(tokensCss).toMatch(/--font-weight-bold\s*:\s*700/);
  });

  test('--card-width is 400px', () => {
    expect(tokensCss).toMatch(/--card-width\s*:\s*400px/);
  });

  test('--input-height is 40px', () => {
    expect(tokensCss).toMatch(/--input-height\s*:\s*40px/);
  });

  test('--transition-fast is 150ms ease', () => {
    expect(tokensCss).toMatch(/--transition-fast\s*:\s*150ms ease/);
  });

  test('--transition-base is 200ms ease', () => {
    expect(tokensCss).toMatch(/--transition-base\s*:\s*200ms ease/);
  });

  test('--transition-slow is 300ms ease', () => {
    expect(tokensCss).toMatch(/--transition-slow\s*:\s*300ms ease/);
  });

  test('--z-index-modal is 300', () => {
    expect(tokensCss).toMatch(/--z-index-modal\s*:\s*300/);
  });

  test('--z-index-toast is 400', () => {
    expect(tokensCss).toMatch(/--z-index-toast\s*:\s*400/);
  });

  test('--branding-logo-size is 48px', () => {
    expect(tokensCss).toMatch(/--branding-logo-size\s*:\s*48px/);
  });

  test('--color-strength-weak is #dc2626', () => {
    expect(tokensCss).toMatch(/--color-strength-weak\s*:\s*#dc2626/);
  });

  test('--color-strength-strong is #16a34a', () => {
    expect(tokensCss).toMatch(/--color-strength-strong\s*:\s*#16a34a/);
  });

  test('composite tokens reference spacing vars', () => {
    expect(tokensCss).toMatch(/--card-padding\s*:\s*var\(--spacing-8\)/);
    expect(tokensCss).toMatch(/--card-gap\s*:\s*var\(--spacing-6\)/);
    expect(tokensCss).toMatch(/--card-border-radius\s*:\s*var\(--radius-lg\)/);
    expect(tokensCss).toMatch(/--input-border-radius\s*:\s*var\(--radius-md\)/);
  });

  test('all tokens are inside :root', () => {
    const rootBlock = tokensCss.match(/:root\s*\{([\s\S]*?)\}/)?.[1] ?? '';
    expect(rootBlock).toContain('--color-accent-primary');
    expect(rootBlock).toContain('--z-index-toast');
  });
});

// ---------------------------------------------------------------------------
// auth.css — class names are present
// ---------------------------------------------------------------------------

describe('auth.css — class definitions are present', () => {
  const expectedClasses = [
    '.auth-page',
    '.auth-branding',
    '.auth-branding__logo',
    '.auth-branding__name',
    '.auth-card',
    '.auth-card__header',
    '.auth-card__title',
    '.auth-card__subtitle',
    '.auth-card__body',
    '.auth-card__footer',
    '.auth-form',
    '.field',
    '.field__label',
    '.field__label--required',
    '.field__input-wrapper',
    '.field__input',
    '.field__input--error',
    '.field__input--with-addon',
    '.field__addon',
    '.field__error',
    '.field__hint',
    '.checkbox',
    '.checkbox__input',
    '.checkbox__label',
    '.checkbox--error',
    '.btn',
    '.btn--primary',
    '.btn--loading',
    '.btn__spinner',
    '.alert',
    '.alert--error',
    '.alert--success',
    '.alert--warning',
    '.alert--info',
    '.alert__icon',
    '.alert__message',
    '.strength-meter',
    '.strength-meter__bars',
    '.strength-meter__bar',
    '.strength-meter--1',
    '.strength-meter--2',
    '.strength-meter--3',
    '.strength-meter--4',
    '.strength-meter__label',
    '.strength-meter__label--weak',
    '.strength-meter__label--fair',
    '.strength-meter__label--good',
    '.strength-meter__label--strong',
    '.auth-link',
    '.auth-divider',
  ];

  test.each(expectedClasses)('defines %s', (cls) => {
    expect(authCss).toContain(cls);
  });
});

// ---------------------------------------------------------------------------
// auth.css — token consumption (var() references)
// ---------------------------------------------------------------------------

describe('auth.css — consumes tokens via var()', () => {
  const expectedVarUsages = [
    'var(--color-bg-page)',
    'var(--color-bg-card)',
    'var(--color-bg-input)',
    'var(--color-bg-input-disabled)',
    'var(--color-border-default)',
    'var(--color-border-focus)',
    'var(--color-border-error)',
    'var(--color-text-primary)',
    'var(--color-text-secondary)',
    'var(--color-text-placeholder)',
    'var(--color-text-disabled)',
    'var(--color-text-inverse)',
    'var(--color-text-link)',
    'var(--color-text-link-hover)',
    'var(--color-error)',
    'var(--color-error-bg)',
    'var(--color-error-border)',
    'var(--color-success)',
    'var(--color-success-bg)',
    'var(--color-success-border)',
    'var(--color-warning)',
    'var(--color-warning-bg)',
    'var(--color-warning-border)',
    'var(--color-info)',
    'var(--color-info-bg)',
    'var(--color-info-border)',
    'var(--color-accent-primary)',
    'var(--color-accent-primary-hover)',
    'var(--color-accent-primary-active)',
    'var(--color-strength-weak)',
    'var(--color-strength-fair)',
    'var(--color-strength-good)',
    'var(--color-strength-strong)',
    'var(--color-strength-empty)',
    'var(--spacing-1)',
    'var(--spacing-2)',
    'var(--spacing-3)',
    'var(--spacing-4)',
    'var(--spacing-5)',
    'var(--spacing-6)',
    'var(--radius-sm)',
    'var(--radius-md)',
    'var(--radius-full)',
    'var(--border-width-default)',
    'var(--border-width-focus)',
    'var(--font-family-sans)',
    'var(--font-size-xs)',
    'var(--font-size-sm)',
    'var(--font-size-md)',
    'var(--font-size-xl)',
    'var(--font-size-2xl)',
    'var(--font-weight-semibold)',
    'var(--font-weight-medium)',
    'var(--font-weight-bold)',
    'var(--line-height-tight)',
    'var(--line-height-normal)',
    'var(--shadow-card)',
    'var(--shadow-sm)',
    'var(--card-width)',
    'var(--card-padding)',
    'var(--card-gap)',
    'var(--card-border-radius)',
    'var(--form-field-gap)',
    'var(--input-height)',
    'var(--input-padding-x)',
    'var(--input-padding-y)',
    'var(--input-border-radius)',
    'var(--transition-fast)',
    'var(--transition-base)',
    'var(--branding-logo-size)',
    'var(--branding-gap)',
  ];

  test.each(expectedVarUsages)('uses %s', (varRef) => {
    expect(authCss).toContain(varRef);
  });
});

// ---------------------------------------------------------------------------
// auth.css — structural / behavioural rules
// ---------------------------------------------------------------------------

describe('auth.css — structural rules', () => {
  test('.auth-page uses flexbox and full viewport height', () => {
    expect(authCss).toMatch(/\.auth-page\s*\{[^}]*display\s*:\s*flex/);
    expect(authCss).toMatch(/\.auth-page\s*\{[^}]*min-height\s*:\s*100vh/);
  });

  test('.auth-card has max-width referencing --card-width', () => {
    expect(authCss).toMatch(/\.auth-card\s*\{[^}]*max-width\s*:\s*var\(--card-width\)/);
  });

  test('.field__input has box-sizing: border-box', () => {
    expect(authCss).toMatch(/\.field__input\s*\{[^}]*box-sizing\s*:\s*border-box/);
  });

  test('.field__input has appearance: none', () => {
    expect(authCss).toMatch(/\.field__input\s*\{[^}]*appearance\s*:\s*none/);
  });

  test('.field__input--error sets error border and background', () => {
    expect(authCss).toMatch(/\.field__input--error\s*\{[^}]*border-color\s*:\s*var\(--color-border-error\)/);
    expect(authCss).toMatch(/\.field__input--error\s*\{[^}]*background-color\s*:\s*var\(--color-error-bg\)/);
  });

  test('.field__label--required::after injects asterisk', () => {
    expect(authCss).toMatch(/\.field__label--required::after\s*\{[^}]*content\s*:\s*['"] \*['"]/);
  });

  test('.btn--primary is full width', () => {
    expect(authCss).toMatch(/\.btn--primary\s*\{[^}]*width\s*:\s*100%/);
  });

  test('.btn--primary:disabled has opacity 0.6', () => {
    expect(authCss).toMatch(/\.btn--primary:disabled\s*\{[^}]*opacity\s*:\s*0\.6/);
  });

  test('.btn--loading disables pointer events', () => {
    expect(authCss).toMatch(/\.btn--loading\s*\{[^}]*pointer-events\s*:\s*none/);
  });

  test('.btn__spinner uses spin animation', () => {
    expect(authCss).toMatch(/\.btn__spinner\s*\{[^}]*animation\s*:[^}]*spin/);
  });

  test('@keyframes spin is defined', () => {
    expect(authCss).toMatch(/@keyframes spin/);
  });

  test('.strength-meter__bars uses CSS grid with 4 columns', () => {
    expect(authCss).toMatch(/\.strength-meter__bars\s*\{[^}]*grid-template-columns\s*:\s*repeat\(4/);
  });

  test('.auth-divider uses pseudo-elements for lines', () => {
    expect(authCss).toMatch(/\.auth-divider::before/);
    expect(authCss).toMatch(/\.auth-divider::after/);
  });

  test('responsive breakpoint at max-width 479px exists', () => {
    expect(authCss).toMatch(/@media\s*\(max-width\s*:\s*479px\)/);
  });

  test('responsive breakpoint at max-width 399px exists', () => {
    expect(authCss).toMatch(/@media\s*\(max-width\s*:\s*399px\)/);
  });

  test('.field__addon is positioned absolute right', () => {
    expect(authCss).toMatch(/\.field__addon\s*\{[^}]*position\s*:\s*absolute/);
    expect(authCss).toMatch(/\.field__addon\s*\{[^}]*right\s*:\s*0/);
  });

  test('.checkbox__input uses accent-color token', () => {
    expect(authCss).toMatch(/\.checkbox__input\s*\{[^}]*accent-color\s*:\s*var\(--color-accent-primary\)/);
  });

  test('.alert has four variants defined', () => {
    expect(authCss).toContain('.alert--error');
    expect(authCss).toContain('.alert--success');
    expect(authCss).toContain('.alert--warning');
    expect(authCss).toContain('.alert--info');
  });

  test('strength meter has four level selectors', () => {
    expect(authCss).toContain('.strength-meter--1');
    expect(authCss).toContain('.strength-meter--2');
    expect(authCss).toContain('.strength-meter--3');
    expect(authCss).toContain('.strength-meter--4');
  });

  test('strength label modifier classes are present', () => {
    expect(authCss).toContain('.strength-meter__label--weak');
    expect(authCss).toContain('.strength-meter__label--fair');
    expect(authCss).toContain('.strength-meter__label--good');
    expect(authCss).toContain('.strength-meter__label--strong');
  });
});

// ---------------------------------------------------------------------------
// Cross-file consistency — every var() used in auth.css is declared in tokens.css
// ---------------------------------------------------------------------------

describe('cross-file — all var() references in auth.css are declared in tokens.css', () => {
  test('no dangling var() references', () => {
    const varRegex = /var\((--[\w-]+)\)/g;
    const missing = [];
    let match;
    // eslint-disable-next-line no-cond-assign
    while ((match = varRegex.exec(authCss)) !== null) {
      const token = match[1];
      if (!tokensCss.includes(token)) {
        missing.push(token);
      }
    }
    expect(missing).toEqual([]);
  });
});
