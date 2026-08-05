const API_BASE = '/api';

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  user: UserDto;
}

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface RegisterResponse {
  accessToken: string;
  user: UserDto;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface UserDto {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface MeResponse {
  user: UserDto;
}

export interface RefreshResponse {
  accessToken: string;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = { error: { code: 'UNKNOWN', message: response.statusText } };
    }
    throw errorData;
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>('POST', '/auth/login', data);
}

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>('POST', '/auth/register', data);
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  return request<void>('POST', '/auth/forgot-password', data);
}

export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  return request<void>('POST', '/auth/reset-password', data);
}

export async function me(): Promise<MeResponse> {
  return request<MeResponse>('GET', '/auth/me');
}

export async function logout(): Promise<void> {
  return request<void>('POST', '/auth/logout');
}

export async function refresh(): Promise<RefreshResponse> {
  return request<RefreshResponse>('POST', '/auth/refresh');
}
