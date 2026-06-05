import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (res.status === 200) {
        NextResponse.redirect(new URL('/login', request.url))
    }
    return NextResponse.json(data, { status: res.status });

  } catch {
    return NextResponse.json({ detail: 'Backend unavailable' }, { status: 503 });
  }
}
