import { Agent, CreateAgentRequest } from '@/types/agent';
import { Task, ActiveGoal, SystemStatus, CreateTaskRequest } from '@/types/task';

const BASE = '/api';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Agents ──────────────────────────────────────────────
export async function getAgents(): Promise<Agent[]> {
  const data = await apiFetch<{ agents: Agent[] }>('/agents');
  return data.agents;
}

export async function getAgent(id: string): Promise<Agent> {
  const data = await apiFetch<{ agent: Agent }>(`/agents/${id}`);
  return data.agent;
}

export async function createAgent(payload: CreateAgentRequest): Promise<Agent> {
  const data = await apiFetch<{ agent: Agent }>('/agents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data.agent;
}

export async function updateAgent(id: string, payload: Partial<CreateAgentRequest>): Promise<Agent> {
  const data = await apiFetch<{ agent: Agent }>(`/agents/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return data.agent;
}

export async function deleteAgent(id: string): Promise<void> {
  await apiFetch(`/agents/${id}`, { method: 'DELETE' });
}

// ── Tasks ────────────────────────────────────────────────
export async function getTasks(status?: string): Promise<Task[]> {
  const query = status ? `?status=${status}` : '';
  const data = await apiFetch<{ tasks: Task[] }>(`/tasks${query}`);
  return data.tasks;
}

export async function getTask(id: string): Promise<Task> {
  const data = await apiFetch<{ task: Task }>(`/tasks/${id}`);
  return data.task;
}

export async function createTask(payload: CreateTaskRequest): Promise<Task> {
  const data = await apiFetch<{ task: Task }>('/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return data.task;
}

export async function updateTask(id: string, payload: Partial<CreateTaskRequest>): Promise<Task> {
  const data = await apiFetch<{ task: Task }>(`/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return data.task;
}

export async function deleteTask(id: string): Promise<void> {
  await apiFetch(`/tasks/${id}`, { method: 'DELETE' });
}

// ── System ───────────────────────────────────────────────
export async function getActiveGoal(): Promise<ActiveGoal> {
  const data = await apiFetch<{ goal: ActiveGoal }>('/tasks?type=goal');
  return data.goal;
}

export async function getSystemStatus(): Promise<SystemStatus> {
  return apiFetch<SystemStatus>('/system/status');
}

// ── Auth ─────────────────────────────────────────────────
export async function login(email: string, password: string): Promise<{ token: string }> {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function signup(email: string, password: string, name: string): Promise<{ token: string }> {
  return apiFetch('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });
}

export async function logout(): Promise<void> {
  await apiFetch('/auth/logout', { method: 'POST' });
}

