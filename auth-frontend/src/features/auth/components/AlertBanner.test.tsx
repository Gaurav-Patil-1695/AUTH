import React from 'react';
import { render, screen } from '@testing-library/react';
import AlertBanner from './AlertBanner';

describe('AlertBanner', () => {
  it('renders the message', () => {
    render(<AlertBanner type="success" message="Operation successful" />);
    expect(screen.getByText('Operation successful')).toBeTruthy();
  });

  it('renders success type with alert-banner--success class', () => {
    const { container } = render(<AlertBanner type="success" message="OK" />);
    expect(container.querySelector('.alert-banner--success')).toBeTruthy();
  });

  it('renders error type with alert-banner--error class', () => {
    const { container } = render(<AlertBanner type="error" message="Failed" />);
    expect(container.querySelector('.alert-banner--error')).toBeTruthy();
  });

  it('uses role="alert" for error type', () => {
    render(<AlertBanner type="error" message="Error occurred" />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('uses role="status" for success type', () => {
    render(<AlertBanner type="success" message="Done" />);
    expect(screen.getByRole('status')).toBeTruthy();
  });

  it('has aria-live="polite"', () => {
    const { container } = render(<AlertBanner type="success" message="msg" />);
    const banner = container.querySelector('.alert-banner');
    expect(banner?.getAttribute('aria-live')).toBe('polite');
  });

  it('has aria-atomic="true"', () => {
    const { container } = render(<AlertBanner type="error" message="msg" />);
    const banner = container.querySelector('.alert-banner');
    expect(banner?.getAttribute('aria-atomic')).toBe('true');
  });

  it('renders icon span with aria-hidden', () => {
    const { container } = render(<AlertBanner type="success" message="msg" />);
    const icon = container.querySelector('.alert-banner__icon');
    expect(icon?.getAttribute('aria-hidden')).toBe('true');
  });

  it('renders message inside alert-banner__message span', () => {
    const { container } = render(<AlertBanner type="error" message="Something went wrong" />);
    expect(container.querySelector('.alert-banner__message')?.textContent).toBe('Something went wrong');
  });

  it('renders alert-banner class on root element', () => {
    const { container } = render(<AlertBanner type="success" message="hi" />);
    expect(container.querySelector('.alert-banner')).toBeTruthy();
  });

  it('renders an svg icon for success', () => {
    const { container } = render(<AlertBanner type="success" message="ok" />);
    expect(container.querySelector('.alert-banner__icon svg')).toBeTruthy();
  });

  it('renders an svg icon for error', () => {
    const { container } = render(<AlertBanner type="error" message="fail" />);
    expect(container.querySelector('.alert-banner__icon svg')).toBeTruthy();
  });
});
