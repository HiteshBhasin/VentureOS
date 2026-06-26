import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { getUser, getToken } from '@/lib/auth';

function Probe() {
  const { user, isAuthenticated, login } = useAuth();
  return (
    <div>
      <span data-testid="email">{user?.email ?? 'none'}</span>
      <span data-testid="authed">{String(isAuthenticated)}</span>
      <button onClick={() => login('a@b.com', 'pw')}>login</button>
    </div>
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe('AuthContext.login', () => {
  // Regression test: the backend returns flat { access_token, user_id, email }
  // fields, not a nested `user` object — login() must build the User itself
  // and update React state, not silently no-op (see AuthContext.tsx fix).
  it('populates user state from the backend flat response shape', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: 'tok-123',
        user_id: 'user-1',
        email: 'a@b.com',
      }),
    } as Response);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    expect(screen.getByTestId('email').textContent).toBe('none');

    await act(async () => {
      screen.getByText('login').click();
    });

    expect(screen.getByTestId('email').textContent).toBe('a@b.com');
    expect(screen.getByTestId('authed').textContent).toBe('true');
    expect(getUser()?.email).toBe('a@b.com');
    expect(getToken()).toBe('tok-123');
  });

  it('throws with the backend detail message on a failed login', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Invalid email or password.' }),
    } as Response);

    let caught: Error | null = null;
    function Thrower() {
      const { login } = useAuth();
      return (
        <button
          onClick={async () => {
            try {
              await login('a@b.com', 'wrong');
            } catch (e) {
              caught = e as Error;
            }
          }}
        >
          go
        </button>
      );
    }

    render(
      <AuthProvider>
        <Thrower />
      </AuthProvider>
    );

    await act(async () => {
      screen.getByText('go').click();
    });

    expect(caught?.message).toBe('Invalid email or password.');
  });
});
