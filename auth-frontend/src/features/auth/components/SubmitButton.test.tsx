import React from 'react';
import { render, screen } from '@testing-library/react';
import SubmitButton from './SubmitButton';

describe('SubmitButton', () => {
  it('renders the label', () => {
    render(<SubmitButton label="Sign In" />);
    expect(screen.getByText('Sign In')).toBeTruthy();
  });

  it('renders a submit button', () => {
    render(<SubmitButton label="Submit" />);
    expect(screen.getByRole('button').getAttribute('type')).toBe('submit');
  });

  it('is not disabled by default', () => {
    render(<SubmitButton label="Submit" />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(false);
  });

  it('is disabled when disabled prop is true', () => {
    render(<SubmitButton label="Submit" disabled />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('is disabled when isLoading is true', () => {
    render(<SubmitButton label="Submit" isLoading />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('does not show spinner by default', () => {
    const { container } = render(<SubmitButton label="Submit" />);
    expect(container.querySelector('.submit-button__spinner')).toBeNull();
  });

  it('shows spinner when isLoading is true', () => {
    const { container } = render(<SubmitButton label="Submit" isLoading />);
    expect(container.querySelector('.submit-button__spinner')).toBeTruthy();
  });

  it('adds submit-button--loading class when isLoading', () => {
    const { container } = render(<SubmitButton label="Submit" isLoading />);
    expect(container.querySelector('.submit-button--loading')).toBeTruthy();
  });

  it('does not add submit-button--loading class when not loading', () => {
    const { container } = render(<SubmitButton label="Submit" />);
    expect(container.querySelector('.submit-button--loading')).toBeNull();
  });

  it('sets aria-busy="true" when loading', () => {
    render(<SubmitButton label="Submit" isLoading />);
    expect(screen.getByRole('button').getAttribute('aria-busy')).toBe('true');
  });

  it('does not set aria-busy when not loading', () => {
    render(<SubmitButton label="Submit" />);
    expect(screen.getByRole('button').getAttribute('aria-busy')).toBeNull();
  });

  it('label text is rendered inside submit-button__label span', () => {
    const { container } = render(<SubmitButton label="Go" />);
    expect(container.querySelector('.submit-button__label')?.textContent).toBe('Go');
  });

  it('is not disabled when isLoading=false and disabled=false', () => {
    render(<SubmitButton label="Submit" isLoading={false} disabled={false} />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(false);
  });
});
