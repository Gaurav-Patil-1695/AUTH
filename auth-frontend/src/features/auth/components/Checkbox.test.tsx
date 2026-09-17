import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Checkbox from './Checkbox';

describe('Checkbox', () => {
  const baseProps = {
    id: 'agree',
    label: 'I agree to terms',
    checked: false,
    onChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the label text', () => {
    render(<Checkbox {...baseProps} />);
    expect(screen.getByText('I agree to terms')).toBeTruthy();
  });

  it('renders checkbox input', () => {
    render(<Checkbox {...baseProps} />);
    expect(screen.getByRole('checkbox')).toBeTruthy();
  });

  it('associates label with input via htmlFor', () => {
    render(<Checkbox {...baseProps} />);
    const label = screen.getByRole('checkbox').closest('label');
    expect(label?.getAttribute('for') ?? label?.htmlFor).toBeTruthy();
  });

  it('reflects checked state', () => {
    render(<Checkbox {...baseProps} checked={true} />);
    expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(true);
  });

  it('reflects unchecked state', () => {
    render(<Checkbox {...baseProps} checked={false} />);
    expect((screen.getByRole('checkbox') as HTMLInputElement).checked).toBe(false);
  });

  it('calls onChange with true when checked', () => {
    const onChange = jest.fn();
    render(<Checkbox {...baseProps} onChange={onChange} checked={false} />);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('calls onChange with false when unchecked', () => {
    const onChange = jest.fn();
    render(<Checkbox {...baseProps} onChange={onChange} checked={true} />);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('shows error message when error provided', () => {
    render(<Checkbox {...baseProps} error="Must accept terms" />);
    expect(screen.getByText('Must accept terms')).toBeTruthy();
  });

  it('error span has role="alert"', () => {
    render(<Checkbox {...baseProps} error="Error" />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('adds checkbox--error class when error present', () => {
    const { container } = render(<Checkbox {...baseProps} error="err" />);
    expect(container.querySelector('.checkbox--error')).toBeTruthy();
  });

  it('does not add checkbox--error class without error', () => {
    const { container } = render(<Checkbox {...baseProps} />);
    expect(container.querySelector('.checkbox--error')).toBeNull();
  });

  it('sets aria-invalid when error present', () => {
    render(<Checkbox {...baseProps} error="err" />);
    expect(screen.getByRole('checkbox').getAttribute('aria-invalid')).toBe('true');
  });

  it('does not set aria-invalid without error', () => {
    render(<Checkbox {...baseProps} />);
    expect(screen.getByRole('checkbox').getAttribute('aria-invalid')).toBeNull();
  });

  it('sets aria-describedby to error id when error present', () => {
    render(<Checkbox {...baseProps} error="err" />);
    expect(screen.getByRole('checkbox').getAttribute('aria-describedby')).toBe('agree-error');
  });

  it('does not set aria-describedby without error', () => {
    render(<Checkbox {...baseProps} />);
    expect(screen.getByRole('checkbox').getAttribute('aria-describedby')).toBeNull();
  });

  it('disables input when disabled', () => {
    render(<Checkbox {...baseProps} disabled />);
    expect((screen.getByRole('checkbox') as HTMLInputElement).disabled).toBe(true);
  });

  it('renders React node as label', () => {
    render(
      <Checkbox
        {...baseProps}
        label={<span data-testid="node-label">Rich label</span>}
      />
    );
    expect(screen.getByTestId('node-label')).toBeTruthy();
  });

  it('renders checkbox__control span', () => {
    const { container } = render(<Checkbox {...baseProps} />);
    expect(container.querySelector('.checkbox__control')).toBeTruthy();
  });
});
