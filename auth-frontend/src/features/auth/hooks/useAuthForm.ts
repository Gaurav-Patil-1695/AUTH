import { useState, useCallback, ChangeEvent, FocusEvent, FormEvent } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FieldValues = Record<string, string>;
export type FieldErrors = Record<string, string>;
export type TouchedFields = Record<string, boolean>;

export type Validator<T extends FieldValues> = (
  values: T
) => Partial<Record<keyof T, string>>;

export interface UseAuthFormOptions<T extends FieldValues> {
  initialValues: T;
  validate: Validator<T>;
  onSubmit: (values: T) => Promise<void>;
}

export interface UseAuthFormReturn<T extends FieldValues> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isSubmitting: boolean;
  submitError: string;
  handleChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleBlur: (e: FocusEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  setSubmitError: (message: string) => void;
  resetForm: () => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuthForm<T extends FieldValues>({
  initialValues,
  validate,
  onSubmit,
}: UseAuthFormOptions<T>): UseAuthFormReturn<T> {
  const [values, setValues] = useState<T>({ ...initialValues });
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Validate a single field after blur
  const validateField = useCallback(
    (name: keyof T, currentValues: T): string => {
      const allErrors = validate(currentValues);
      return (allErrors[name] as string) ?? '';
    },
    [validate]
  );

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { name, value, type, checked } = e.target;
      const newValue = type === 'checkbox' ? (checked ? 'true' : 'false') : value;

      setValues((prev) => {
        const next = { ...prev, [name]: newValue } as T;

        // Re-validate the field if it has already been touched
        setErrors((prevErrors) => {
          if (touched[name as keyof T]) {
            const fieldError = validateField(name as keyof T, next);
            return { ...prevErrors, [name]: fieldError };
          }
          return prevErrors;
        });

        return next;
      });

      // Clear a stale submit-level error once the user starts editing
      if (submitError) {
        setSubmitError('');
      }
    },
    [touched, validateField, submitError]
  );

  const handleBlur = useCallback(
    (e: FocusEvent<HTMLInputElement>) => {
      const { name } = e.target;

      setTouched((prev) => ({ ...prev, [name]: true }));

      setErrors((prev) => {
        const fieldError = validateField(name as keyof T, values);
        return { ...prev, [name]: fieldError };
      });
    },
    [values, validateField]
  );

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      // Mark all fields as touched so every error becomes visible
      const allTouched = Object.keys(values).reduce<Partial<Record<keyof T, boolean>>>(
        (acc, key) => ({ ...acc, [key]: true }),
        {}
      );
      setTouched(allTouched);

      // Run full validation
      const allErrors = validate(values);
      setErrors(allErrors);

      const hasErrors = Object.values(allErrors).some((msg) => !!msg);
      if (hasErrors) {
        return;
      }

      setIsSubmitting(true);
      setSubmitError('');

      try {
        await onSubmit(values);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setSubmitError(err.message);
        } else {
          setSubmitError('An unexpected error occurred. Please try again.');
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validate, onSubmit]
  );

  const resetForm = useCallback(() => {
    setValues({ ...initialValues });
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
    setSubmitError('');
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    handleChange,
    handleBlur,
    handleSubmit,
    setSubmitError,
    resetForm,
  };
}
