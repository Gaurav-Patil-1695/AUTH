import { renderHook, act } from '@testing-library/react';
import { useAuthForm, FieldValues, Validator } from './useAuthForm';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type LoginValues = { email: string; password: string };

const initialValues: LoginValues = { email: '', password: '' };

const validate: Validator<LoginValues> = (values) => {
  const errors: Partial<Record<keyof LoginValues, string>> = {};
  if (!values.email) errors.email = 'Email is required';
  if (!values.password) errors.password = 'Password is required';
  return errors;
};

function makeEvent(
  name: string,
  value: string,
  type = 'text'
): React.ChangeEvent<HTMLInputElement> {
  return {
    target: { name, value, type, checked: false },
  } as unknown as React.ChangeEvent<HTMLInputElement>;
}

function makeBlurEvent(name: string): React.FocusEvent<HTMLInputElement> {
  return { target: { name } } as unknown as React.FocusEvent<HTMLInputElement>;
}

function makeSubmitEvent(): React.FormEvent<HTMLFormElement> {
  return { preventDefault: jest.fn() } as unknown as React.FormEvent<HTMLFormElement>;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useAuthForm', () => {
  // --- initial state -------------------------------------------------------

  it('initialises with the supplied initial values', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    expect(result.current.values).toEqual({ email: '', password: '' });
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.submitError).toBe('');
  });

  // --- handleChange --------------------------------------------------------

  it('updates the field value on change', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    act(() => {
      result.current.handleChange(makeEvent('email', 'user@example.com'));
    });

    expect(result.current.values.email).toBe('user@example.com');
  });

  it('handles checkbox change (checked = true → "true")', () => {
    type CheckboxValues = { remember: string };
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues: { remember: 'false' },
        validate: () => ({}),
        onSubmit: jest.fn(),
      })
    );

    const checkboxEvent = {
      target: { name: 'remember', value: '', type: 'checkbox', checked: true },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleChange(checkboxEvent);
    });

    expect(result.current.values.remember).toBe('true');
  });

  it('handles checkbox change (checked = false → "false")', () => {
    const { result } = renderHook(() =>
      useAuthForm({
        initialValues: { remember: 'true' },
        validate: () => ({}),
        onSubmit: jest.fn(),
      })
    );

    const checkboxEvent = {
      target: { name: 'remember', value: '', type: 'checkbox', checked: false },
    } as unknown as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleChange(checkboxEvent);
    });

    expect(result.current.values.remember).toBe('false');
  });

  it('re-validates a touched field on change', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    // Touch the email field so re-validation is triggered
    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
    });

    // Errors for email should be set
    expect(result.current.errors.email).toBe('Email is required');

    // Now type a valid value
    act(() => {
      result.current.handleChange(makeEvent('email', 'user@example.com'));
    });

    // Error should be cleared
    expect(result.current.errors.email).toBe('');
  });

  it('does not re-validate an untouched field on change', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    act(() => {
      result.current.handleChange(makeEvent('email', ''));
    });

    // Field was never touched, so errors should remain empty
    expect(result.current.errors.email).toBeUndefined();
  });

  it('clears submitError when user starts typing', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    act(() => {
      result.current.setSubmitError('Login failed');
    });

    expect(result.current.submitError).toBe('Login failed');

    act(() => {
      result.current.handleChange(makeEvent('email', 'x'));
    });

    expect(result.current.submitError).toBe('');
  });

  // --- handleBlur ----------------------------------------------------------

  it('marks field as touched on blur', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
    });

    expect(result.current.touched.email).toBe(true);
  });

  it('sets field error on blur for an invalid value', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
    });

    expect(result.current.errors.email).toBe('Email is required');
  });

  it('clears field error on blur for a valid value', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    // Set a valid email value first
    act(() => {
      result.current.handleChange(makeEvent('email', 'user@example.com'));
    });

    act(() => {
      result.current.handleBlur(makeBlurEvent('email'));
    });

    expect(result.current.errors.email).toBe('');
  });

  // --- handleSubmit --------------------------------------------------------

  it('calls preventDefault on submit', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    const event = makeSubmitEvent();

    await act(async () => {
      result.current.handleSubmit(event);
    });

    expect(event.preventDefault).toHaveBeenCalled();
  });

  it('marks all fields as touched on submit', async () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    expect(result.current.touched).toEqual({ email: true, password: true });
  });

  it('does not call onSubmit when there are validation errors', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(result.current.errors.email).toBe('Email is required');
    expect(result.current.errors.password).toBe('Password is required');
  });

  it('calls onSubmit with form values when validation passes', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    // Fill in valid values
    act(() => {
      result.current.handleChange(makeEvent('email', 'user@example.com'));
      result.current.handleChange(makeEvent('password', 'secret123'));
    });

    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'secret123',
    });
  });

  it('sets isSubmitting to true while onSubmit is pending', async () => {
    let resolveSubmit!: () => void;
    const onSubmit = jest.fn(
      () => new Promise<void>((res) => { resolveSubmit = res; })
    );

    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    act(() => {
      result.current.handleChange(makeEvent('email', 'u@example.com'));
      result.current.handleChange(makeEvent('password', 'pass'));
    });

    // Start submit without awaiting
    act(() => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    expect(result.current.isSubmitting).toBe(true);

    // Resolve the submit and verify isSubmitting goes back to false
    await act(async () => {
      resolveSubmit();
    });

    expect(result.current.isSubmitting).toBe(false);
  });

  it('sets submitError from Error instance thrown by onSubmit', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('Invalid credentials'));
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    act(() => {
      result.current.handleChange(makeEvent('email', 'u@example.com'));
      result.current.handleChange(makeEvent('password', 'pass'));
    });

    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    expect(result.current.submitError).toBe('Invalid credentials');
    expect(result.current.isSubmitting).toBe(false);
  });

  it('sets generic submitError for non-Error throws from onSubmit', async () => {
    const onSubmit = jest.fn().mockRejectedValue('some string error');
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    act(() => {
      result.current.handleChange(makeEvent('email', 'u@example.com'));
      result.current.handleChange(makeEvent('password', 'pass'));
    });

    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    expect(result.current.submitError).toBe(
      'An unexpected error occurred. Please try again.'
    );
  });

  // --- setSubmitError ------------------------------------------------------

  it('allows manually setting a submitError', () => {
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit: jest.fn() })
    );

    act(() => {
      result.current.setSubmitError('Custom error');
    });

    expect(result.current.submitError).toBe('Custom error');
  });

  // --- resetForm -----------------------------------------------------------

  it('resets all state back to initial values', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('Fail'));
    const { result } = renderHook(() =>
      useAuthForm({ initialValues, validate, onSubmit })
    );

    // Make changes
    act(() => {
      result.current.handleChange(makeEvent('email', 'u@example.com'));
      result.current.handleChange(makeEvent('password', 'pass'));
    });

    await act(async () => {
      result.current.handleSubmit(makeSubmitEvent());
    });

    // State has changed; now reset
    act(() => {
      result.current.resetForm();
    });

    expect(result.current.values).toEqual({ email: '', password: '' });
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.submitError).toBe('');
  });
});
