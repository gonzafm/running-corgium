import { apiClient } from './client';
import type { LoginResponse, UserRead } from './types';

export const authApi = {
  login: (email: string, password: string): Promise<LoginResponse> => {
    return apiClient.postForm<LoginResponse>('/auth/jwt/login', {
      username: email,
      password,
    });
  },

  register: (email: string, password: string): Promise<UserRead> => {
    return apiClient.post<UserRead>('/auth/register', { email, password });
  },

  getMe: (): Promise<UserRead> => {
    return apiClient.get<UserRead>('/users/me');
  },

  logout: (): Promise<void> => {
    return apiClient.postEmpty('/auth/jwt/logout');
  },
};
