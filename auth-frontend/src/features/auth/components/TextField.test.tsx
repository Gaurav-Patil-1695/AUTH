import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TextField from './TextField';

describe('TextField', () => {
  const baseProps = {
    id: 'test-field',
    label: 'Test Label',
    value: '',
    onChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the label', () => {
    render(<TextField {...baseProps} />);
    expect(screen.getByText('Test Label')).toBeTruthy();
  });

  it('associates label with input via htmlFor', () => {
    render(<TextField {...baseProps} />);
    const label = screen.getByText('Test Label');
    expect(label.closest('label')?.getAttribute('for')).toBe('test-field');
  });

  it('renders input with correct id', () => {
    render(<TextField {...baseProps} />);
    expect(screen.getByRole('textbox')).toBeTruthy();
    expect(screen.getByRole('textbox').getAttribute('id')).toBe('test-field');
  });

  it('defaults type to text', () => {
    render(<TextField {...baseProps} />);
    expect(screen.getByRole('textbox').getAttribute('type')).toBe('text');
  });

  it('sets type to email when specified', () => {
    render(<TextField {...baseProps} type="email" />);
    expect(screen.getByRole('textbox').getAttribute('type')).toBe('email');
  });

  it('calls onChange with the input value', () => {
    const onChange = jest.fn();
    render(<TextField {...baseProps} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } });
    expect(onChange).toHaveBeenCalledWith('hello');
  });

  it('displays the current value', () => {
    render(<TextField {...baseProps} value="prefilled" />);
    expect((screen.getByRole('textbox') as HTMLInputElement).value).toBe('prefilled');
  });

  it('shows required asterisk when required', () => {
    render(<TextField {...baseProps} required />);
    expect(screen.getByText('*', { exact: false })).toBeTruthy();
  });

  it('does not show required asterisk when not required', () => {
    const { container } = render(<TextField {...baseProps} />);
    expect(container.querySelector('.field__required')).toBeNull();
  });

  it('shows hint text when provided', () => {
    render(<TextField {...baseProps} hint="Some hint" />);
    expect(screen.getByText('Some hint')).toBeTruthy();
  });

  it('hides hint when error is present', () => {
    render(<TextField {...baseProps} hint="Some hint" error="Bad input" />);
    expect(screen.queryByText('Some hint')).toBeNull();
  });

  it('shows error message when error is provided', () => {
    render(<TextField {...baseProps} error="This field is required" />);
    expect(screen.getByText('This field is required')).toBeTruthy();
  });

  it('error span has role="alert"', () => {
    render(<TextField {...baseProps} error="Error msg" />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('adds field--error class when error is present', () => {
    const { container } = render(<TextField {...baseProps} error="err" />);
    expect(container.querySelector('.field--error')).toBeTruthy();
  });

  it('does not add field--error class without error', () => {
    const { container } = render(<TextField {...baseProps} />);
    expect(container.querySelector('.field--error')).toBeNull();
  });

  it('sets aria-invalid when error is present', () => {
    render(<TextField {...baseProps} error="err" />);
    expect(screen.getByRole('textbox').getAttribute('aria-invalid')).toBe('true');
  });

  it('does not set aria-invalid without error', () => {
    render(<TextField {...baseProps} />);
    expect(screen.getByRole('textbox').getAttribute('aria-invalid')).toBeNull();
  });

  it('sets aria-describedby to hint id when hint present', () => {
    render(<TextField {...baseProps} hint="hint text" />);
    expect(screen.getByRole('textbox').getAttribute('aria-describedby')).toBe('test-field-hint');
  });

  it('sets aria-describedby to error id when error present', () => {
    render(<TextField {...baseProps} error="err" />);
    expect(screen.getByRole('textbox').getAttribute('aria-describedby')).toBe('test-field-error');
  });

  it('sets aria-describedby to both when hint and error present', () => {
    render(<TextField {...baseProps} hint="hint" error="err" />);
    const describedBy = screen.getByRole('textbox').getAttribute('aria-describedby');
    expect(describedBy).toContain('test-field-hint');
    expect(describedBy).toContain('test-field-error');
  });

  it('does not set aria-describedby when no hint or error', () => {
    render(<TextField {...baseProps} />);
    expect(screen.getByRole('textbox').getAttribute('aria-describedby')).toBeNull();
  });

  it('passes disabled prop to input', () => {
    render(<TextField {...baseProps} disabled />);
    expect((screen.getByRole('textbox') as HTMLInputElement).disabled).toBe(true);
  });

  it('passes placeholder prop to input', () => {
    render(<TextField {...baseProps} placeholder="Enter text" />);
    expect(screen.getByRole('textbox').getAttribute('placeholder')).toBe('Enter text');
  });

  it('passes autoComplete prop to input', () => {
    render(<TextField {...baseProps} autoComplete="email" />);
    expect(screen.getByRole('textbox').getAttribute('autocomplete')).toBe('email');
  });
});
