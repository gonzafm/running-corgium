import { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { authApi } from '../api/auth';
import { apiClient } from '../api/client';
import type { UserRead } from '../api/types';
import { AuthContext } from '../hooks/useAuth';

export interface AuthState {
  token: string | null;
  user: UserRead | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const TOKEN_KEY = 'auth_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  const clearAuth = useCallback(() => {
    console.log('[Auth] Clearing auth state');
    setToken(null);
    setUser(null);
    apiClient.clearToken();
    localStorage.removeItem(TOKEN_KEY);
  }, []);

  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (!savedToken) {
      console.log('[Auth] No saved token found');
      setLoading(false);
      return;
    }

    console.log('[Auth] Found saved token, validating...');
    apiClient.setToken(savedToken);
    authApi
      .getMe()
      .then((userData) => {
        console.log('[Auth] Token valid, user:', userData.email);
        setToken(savedToken);
        setUser(userData);
      })
      .catch((err) => {
        console.warn('[Auth] Saved token invalid, clearing:', err.message);
        clearAuth();
      })
      .finally(() => {
        setLoading(false);
      });
  }, [clearAuth]);

  const login = useCallback(async (email: string, password: string) => {
    console.log('[Auth] Logging in:', email);
    const response = await authApi.login(email, password);
    const newToken = response.access_token;
    localStorage.setItem(TOKEN_KEY, newToken);
    apiClient.setToken(newToken);
    setToken(newToken);
    const userData = await authApi.getMe();
    console.log('[Auth] Login successful, user:', userData.email);
    setUser(userData);
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      console.log('[Auth] Registering:', email);
      await authApi.register(email, password);
      console.log('[Auth] Registration successful, logging in...');
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    console.log('[Auth] Logging out');
    try {
      await authApi.logout();
    } finally {
      clearAuth();
    }
  }, [clearAuth]);

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token && !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
