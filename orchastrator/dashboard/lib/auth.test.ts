import { describe, it, expect, beforeEach } from 'vitest';
import { setToken, getToken, removeToken, setUser, getUser, isAuthenticated, logout } from './auth';
import { User } from '@/types/api';

const user: User = { id: '1', email: 'a@b.com', name: 'A', role: 'user', createdAt: '2024-01-01' };

beforeEach(() => {
  localStorage.clear();
});

describe('token storage', () => {
  it('round-trips a token through localStorage', () => {
    expect(getToken()).toBeNull();
    setToken('abc123');
    expect(getToken()).toBe('abc123');
    removeToken();
    expect(getToken()).toBeNull();
  });
});

describe('user storage', () => {
  it('round-trips a user through localStorage', () => {
    expect(getUser()).toBeNull();
    setUser(user);
    expect(getUser()).toEqual(user);
  });

  it('returns null for malformed stored JSON', () => {
    localStorage.setItem('venture_os_user', '{not json');
    expect(getUser()).toBeNull();
  });
});

describe('isAuthenticated / logout', () => {
  it('is false with no token, true once set, false after logout', () => {
    expect(isAuthenticated()).toBe(false);
    setToken('abc123');
    setUser(user);
    expect(isAuthenticated()).toBe(true);
    logout();
    expect(isAuthenticated()).toBe(false);
    expect(getUser()).toBeNull();
  });
});
