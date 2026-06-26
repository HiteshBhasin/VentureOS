import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

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
    const res = await tryBackend('/memory', { headers: { Authorization: auth } });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ memories: [], source: 'unavailable' });
  }
}
