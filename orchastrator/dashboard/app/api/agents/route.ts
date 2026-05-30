import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

const MOCK_AGENTS = [
  {
    id: 'sl-001',
    name: 'STRATEGY_LEAD',
    type: 'research',
    status: 'active',
    activity: 'THINKING',
    progress: 82,
    description: 'Refining core value propositions and aligning with growth levers...',
    tokens_per_sec: 1248,
    cost_estimate: 0.14,
    model: 'gpt-4o',
  },
  {
    id: 'mr-001',
    name: 'MARKET_RESEARCHER',
    type: 'research',
    status: 'active',
    activity: 'SCRAPING',
    progress: 34,
    description: 'Extracting pricing models from 12 tier-1 competitors.',
    tokens_per_sec: 0,
    cost_estimate: 0,
    model: 'gpt-4o',
  },
];

async function tryBackend(path: string, init?: RequestInit) {
  const res = await fetch(`${BACKEND}/api/v1${path}`, {
    ...init,
    signal: AbortSignal.timeout(3000),
  });
  return res;
}

export async function GET(request: NextRequest) {
  const auth = request.headers.get('Authorization') ?? '';
  try {
    const res = await tryBackend('/agents', { headers: { Authorization: auth } });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ agents: MOCK_AGENTS, source: 'mock' });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const auth = request.headers.get('Authorization') ?? '';
    const res = await tryBackend('/agents', {
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

