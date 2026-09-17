import React from 'react';
import { render, screen } from '@testing-library/react';
import Branding from './Branding';

describe('Branding', () => {
  it('renders the AuthStarter wordmark', () => {
    render(<Branding />);
    expect(screen.getByText('AuthStarter')).toBeTruthy();
  });

  it('renders the branding container', () => {
    const { container } = render(<Branding />);
    expect(container.querySelector('.branding')).toBeTruthy();
  });

  it('renders the logo div', () => {
    const { container } = render(<Branding />);
    expect(container.querySelector('.branding__logo')).toBeTruthy();
  });

  it('renders the logo icon svg', () => {
    const { container } = render(<Branding />);
    expect(container.querySelector('.branding__logo-icon')).toBeTruthy();
  });

  it('logo div has aria-hidden="true"', () => {
    const { container } = render(<Branding />);
    const logoDiv = container.querySelector('.branding__logo');
    expect(logoDiv?.getAttribute('aria-hidden')).toBe('true');
  });

  it('renders the wordmark text span', () => {
    const { container } = render(<Branding />);
    expect(container.querySelector('.branding__wordmark-text')).toBeTruthy();
  });
});
