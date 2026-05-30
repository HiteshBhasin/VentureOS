import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

const MOCK_TASKS = [
  {
    id: 'task-001',
    title: 'Competitor Analysis',
    description: 'Scraped top 5 competitors, identified feature gaps and pricing models.',
    status: 'completed',
    priority: 'high',
    progress: 100,
    tags: ['Node_AI', 'Flow Data'],
    agent_id: 'mr-001',
    created_at: new Date(Date.now() - 14 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  },
  {
    id: 'task-002',
    title: 'User Persona Creation',
    description: 'Synthesizing behavioral patterns from competitor analysis to define 3 target archetypes.',
    status: 'running',
    priority: 'high',
    progress: 7,
    tags: ['Initiating_Decomposit...'],
    agent_id: 'sl-001',
    created_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'task-003',
    title: 'Ad Copy Generation',
    description: 'Waiting for persona completion to generate tailored ad copy variants for LinkedIn and Google.',
    status: 'queued',
    priority: 'medium',
    progress: 0,
    tags: [],
    agent_id: null,
    created_at: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
  },
];

const MOCK_ACTIVE_GOAL = {
  id: 'goal-001',
  title: 'Build a marketing strategy for a SaaS product',
  status: 'executing',
  completion: 33,
  elapsed_seconds: 866,   // 14m 22s
  pid: 48821,
  memory_used_gb: 2.4,
  memory_total_gb: 32,
};

async function tryBackend(path: string, init?: RequestInit) {
  const res = await fetch(`${BACKEND}/api/v1${path}`, {
    ...init,
    signal: AbortSignal.timeout(3000),
  });
  return res;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type');
  const auth = request.headers.get('Authorization') ?? '';
  const authHeader = { Authorization: auth };

  // Return active goal info when ?type=goal
  if (type === 'goal') {
    try {
      const res = await tryBackend('/system/goal', { headers: authHeader });
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    } catch {
      return NextResponse.json({ goal: MOCK_ACTIVE_GOAL, source: 'mock' });
    }
  }

  try {
    const status = searchParams.get('status');
    const query = status ? `?status=${status}` : '';
    const res = await tryBackend(`/tasks${query}`, { headers: authHeader });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ tasks: MOCK_TASKS, source: 'mock' });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const auth = request.headers.get('Authorization') ?? '';
    const res = await tryBackend('/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': auth },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}

