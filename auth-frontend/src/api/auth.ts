const API_BASE_URL = process.env.REACT_APP_API_BASE_URL ?? 'http://localhost:8000';

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
}

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export interface RegisterResponse {
  accessToken: string;
  tokenType: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface MeResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LogoutResponse {
  message: string;
}

export interface RefreshResponse {
  accessToken: string;
  tokenType: string;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  accessToken?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let message = 'Invalid email or password.';
    try {
      const data = await response.json();
      if (data?.error?.message) {
        message = data.error.message;
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }

  const text = await response.text();
  if (!text) {
    return undefined as unknown as T;
  }
  return JSON.parse(text) as T;
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>('POST', '/auth/login', {
    email: payload.email,
    password: payload.password,
    remember_me: payload.rememberMe,
  });
}

export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>('POST', '/auth/register', {
    full_name: payload.fullName,
    email: payload.email,
    password: payload.password,
    confirm_password: payload.confirmPassword,
    accept_terms: payload.acceptTerms,
  });
}

export async function forgotPassword(
  payload: ForgotPasswordRequest,
): Promise<ForgotPasswordResponse> {
  return request<ForgotPasswordResponse>('POST', '/auth/forgot-password', {
    email: payload.email,
  });
}

export async function resetPassword(
  payload: ResetPasswordRequest,
): Promise<ResetPasswordResponse> {
  return request<ResetPasswordResponse>('POST', '/auth/reset-password', {
    token: payload.token,
    password: payload.password,
    confirm_password: payload.confirmPassword,
  });
}

export async function me(accessToken: string): Promise<MeResponse> {
  return request<MeResponse>('GET', '/auth/me', undefined, accessToken);
}

export async function logout(accessToken: string): Promise<LogoutResponse> {
  return request<LogoutResponse>('POST', '/auth/logout', undefined, accessToken);
}

export async function refresh(): Promise<RefreshResponse> {
  return request<RefreshResponse>('POST', '/auth/refresh');
}
