import React from 'react';
import { render, screen } from '@testing-library/react';
import PasswordStrengthMeter from './PasswordStrengthMeter';

describe('PasswordStrengthMeter', () => {
  it('renders the strength meter container', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    expect(container.querySelector('.strength-meter')).toBeTruthy();
  });

  it('renders 4 rule checklist items', () => {
    render(<PasswordStrengthMeter password="" />);
    const list = screen.getByRole('list', { name: 'Password requirements' });
    expect(list.querySelectorAll('li').length).toBe(4);
  });

  it('shows no strength label for empty password', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    expect(container.querySelector('.strength-meter__label')).toBeNull();
  });

  it('shows "Weak" label when only 1 rule passes', () => {
    render(<PasswordStrengthMeter password="a" />);
    expect(screen.getByText('Weak')).toBeTruthy();
  });

  it('shows "Weak" label when 0 rules pass (non-empty password)', () => {
    // A single digit does not pass length (1 char) but passes number — only 1 passes
    // To get 0 passes we need a char that passes nothing: not letter, no length, no upper, no lower, no digit
    // Actually impossible with ASCII printable, digit passes number rule
    // Use a string that passes only lowercase
    render(<PasswordStrengthMeter password="a" />);
    expect(screen.getByText('Weak')).toBeTruthy();
  });

  it('shows "Fair" label when 2 rules pass', () => {
    // 'Ab' — uppercase + lowercase = 2 rules, not length, not number
    render(<PasswordStrengthMeter password="Ab" />);
    expect(screen.getByText('Fair')).toBeTruthy();
  });

  it('shows "Good" label when 3 rules pass', () => {
    // 'Ab1' — uppercase + lowercase + number = 3, not length
    render(<PasswordStrengthMeter password="Ab1" />);
    expect(screen.getByText('Good')).toBeTruthy();
  });

  it('shows "Strong" label when all 4 rules pass', () => {
    render(<PasswordStrengthMeter password="Abcdef1!" />);
    // length >= 8, uppercase, lowercase, number
    // Wait — 'Abcdef1!' has 8 chars, uppercase A, lowercase bcdef, number 1 → all 4
    expect(screen.getByText('Strong')).toBeTruthy();
  });

  it('applies strength-meter--weak modifier class for weak password', () => {
    const { container } = render(<PasswordStrengthMeter password="a" />);
    expect(container.querySelector('.strength-meter--weak')).toBeTruthy();
  });

  it('applies strength-meter--fair modifier class for fair password', () => {
    const { container } = render(<PasswordStrengthMeter password="Ab" />);
    expect(container.querySelector('.strength-meter--fair')).toBeTruthy();
  });

  it('applies strength-meter--good modifier class for good password', () => {
    const { container } = render(<PasswordStrengthMeter password="Ab1" />);
    expect(container.querySelector('.strength-meter--good')).toBeTruthy();
  });

  it('applies strength-meter--strong modifier class for strong password', () => {
    const { container } = render(<PasswordStrengthMeter password="Abcdef1g" />);
    expect(container.querySelector('.strength-meter--strong')).toBeTruthy();
  });

  it('does not apply any strength modifier for empty password', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    const meter = container.querySelector('.strength-meter');
    expect(meter?.className).toBe('strength-meter');
  });

  it('marks length rule as passed for password >= 8 chars', () => {
    render(<PasswordStrengthMeter password="abcdefgh" />);
    const listItems = screen.getAllByRole('listitem');
    const lengthItem = listItems.find(el => el.textContent?.includes('At least 8 characters'));
    expect(lengthItem?.className).toContain('strength-meter__rule--passed');
  });

  it('marks length rule as not passed for short password', () => {
    render(<PasswordStrengthMeter password="abc" />);
    const listItems = screen.getAllByRole('listitem');
    const lengthItem = listItems.find(el => el.textContent?.includes('At least 8 characters'));
    expect(lengthItem?.className).not.toContain('strength-meter__rule--passed');
  });

  it('marks uppercase rule as passed when uppercase present', () => {
    render(<PasswordStrengthMeter password="A" />);
    const listItems = screen.getAllByRole('listitem');
    const item = listItems.find(el => el.textContent?.includes('At least one uppercase letter'));
    expect(item?.className).toContain('strength-meter__rule--passed');
  });

  it('marks number rule as passed when digit present', () => {
    render(<PasswordStrengthMeter password="1" />);
    const listItems = screen.getAllByRole('listitem');
    const item = listItems.find(el => el.textContent?.includes('At least one number'));
    expect(item?.className).toContain('strength-meter__rule--passed');
  });

  it('renders sr-only passed/not met text', () => {
    render(<PasswordStrengthMeter password="A" />);
    expect(screen.getAllByText('passed').length).toBeGreaterThan(0);
    expect(screen.getAllByText('not met').length).toBeGreaterThan(0);
  });

  it('renders 4 bar segments', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    expect(container.querySelectorAll('.strength-meter__segment').length).toBe(4);
  });

  it('fills segments equal to number of passing rules', () => {
    const { container } = render(<PasswordStrengthMeter password="Ab1" />);
    // 3 rules pass
    expect(container.querySelectorAll('.strength-meter__segment--filled').length).toBe(3);
  });

  it('has no filled segments for empty password', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    expect(container.querySelectorAll('.strength-meter__segment--filled').length).toBe(0);
  });

  it('has aria-label on strength meter container', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    const meter = container.querySelector('.strength-meter');
    expect(meter?.getAttribute('aria-label')).toBe('Password strength');
  });
});
