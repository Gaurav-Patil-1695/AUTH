import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface RegisterResponse {
  id: string;
  fullName: string;
  email: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  user: {
    id: string;
    fullName: string;
    email: string;
  };
}

export interface MeResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface RefreshResponse {
  accessToken: string;
}

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const response = await api.post<RegisterResponse>('/auth/register', {
    fullName: data.fullName,
    email: data.email,
    password: data.password,
    confirmPassword: data.confirmPassword,
  });
  return response.data;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', {
    email: data.email,
    password: data.password,
    rememberMe: data.rememberMe ?? false,
  });
  return response.data;
}

export async function me(): Promise<MeResponse> {
  const response = await api.get<MeResponse>('/auth/me');
  return response.data;
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout');
}

export async function refresh(): Promise<RefreshResponse> {
  const response = await api.post<RefreshResponse>('/auth/refresh');
  return response.data;
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  await api.post('/auth/forgot-password', { email: data.email });
}

export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  await api.post('/auth/reset-password', {
    token: data.token,
    password: data.password,
    confirmPassword: data.confirmPassword,
  });
}

export default api;
