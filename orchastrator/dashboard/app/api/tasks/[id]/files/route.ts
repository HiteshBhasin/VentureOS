import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const auth = request.headers.get('Authorization') ?? '';
  try {
    const res = await fetch(`${BACKEND}/api/v1/tasks/${id}/files`, {
      headers: { Authorization: auth },
      signal: AbortSignal.timeout(5000),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Backend unavailable' }, { status: 503 });
  }
}
