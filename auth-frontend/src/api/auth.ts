const API_BASE = '/api';

export interface RegisterPayload {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface UserResponse {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  fullName?: string;
  isActive?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface AuthTokenResponse {
  accessToken: string;
  tokenType: string;
  user: UserResponse;
}

export interface MessageResponse {
  message: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorData: ApiError;
    try {
      errorData = await response.json();
    } catch {
      throw new Error(`HTTP error ${response.status}`);
    }
    throw errorData;
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export async function register(payload: RegisterPayload): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>('POST', '/auth/register', {
    full_name: payload.fullName,
    email: payload.email,
    password: payload.password,
    confirm_password: payload.confirmPassword,
  });
}

export async function login(payload: LoginPayload): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>('POST', '/auth/login', {
    email: payload.email,
    password: payload.password,
    remember_me: payload.rememberMe ?? false,
  });
}

export async function forgotPassword(payload: ForgotPasswordPayload): Promise<MessageResponse> {
  return request<MessageResponse>('POST', '/auth/forgot-password', {
    email: payload.email,
  });
}

export async function resetPassword(payload: ResetPasswordPayload): Promise<MessageResponse> {
  return request<MessageResponse>('POST', '/auth/reset-password', {
    token: payload.token,
    password: payload.password,
    confirm_password: payload.confirmPassword,
  });
}

export async function me(): Promise<UserResponse> {
  return request<UserResponse>('GET', '/auth/me');
}

export async function logout(): Promise<void> {
  return request<void>('POST', '/auth/logout');
}

export async function refresh(): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>('POST', '/auth/refresh');
}
