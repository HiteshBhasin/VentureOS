import { User } from '@/types/api';

export function setToken(token: string): void;
export function getToken(): string | null;
export function removeToken(): void;
export function setUser(user: User): void;
export function getUser(): User | null;
export function removeUser(): void;
export function isAuthenticated(): boolean;
export function logout(): void;
