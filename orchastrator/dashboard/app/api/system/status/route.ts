import { NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

const MOCK_STATUS = {
  active_agents: 12,
  tokens_per_sec: 1248,
  cost_estimate: 0.14,
  memory_used_gb: 2.4,
  memory_total_gb: 32,
  uptime_seconds: 252,
  latency_ms: 42,
};

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/v1/system/status`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ ...MOCK_STATUS, source: 'mock' });
  }
}
