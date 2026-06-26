'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { User } from '@/types/api';
import {
  getToken as readToken,
  getUser as readUser,
  setToken,
  setUser as writeUser,
  logout as clearAuth,
  isAuthenticated as checkAuth,
} from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(() =>
    typeof window !== 'undefined' ? readToken() : null
  );
  const [user, setUserState] = useState<User | null>(() =>
    typeof window !== 'undefined' ? readUser() : null
  );

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? 'Login failed');
    }
    const data = await res.json();
    setToken(data.access_token);
    const loggedInUser: User = { id: data.user_id, email: data.email, name: '', role: 'user', createdAt: new Date().toISOString() };
    writeUser(loggedInUser);
    setUserState(loggedInUser);
    setTokenState(data.access_token);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setTokenState(null);
    setUserState(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token && checkAuth(), login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export { AuthContext };
