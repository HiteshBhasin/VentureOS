import { NextRequest } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

// Fallback log lines shown when backend is offline
const FALLBACK_LOGS = [
  '[OK] ORCHESTRATOR ONLINE — BACKEND UNREACHABLE',
  '[PROC] ATTEMPTING RECONNECT TO AGENT ENGINE...',
  '[...] WAITING FOR BACKEND AT localhost:8000',
  '[PROC] RETRY IN PROGRESS...',
  '[OK] SYSTEM NOMINAL — AWAITING BACKEND CONNECTION',
];

export async function GET(request: NextRequest) {
  const auth = request.headers.get('Authorization')
    ?? (request.nextUrl.searchParams.get('token')
        ? `Bearer ${request.nextUrl.searchParams.get('token')}`
        : '');

  // Try to proxy the real backend SSE stream
  try {
    const upstream = await fetch(`${BACKEND}/api/v1/system/stream`, {
      headers: { Authorization: auth },
      signal: AbortSignal.timeout(3000),
    });
    if (upstream.ok && upstream.body) {
      // Pipe backend stream through; abort when client disconnects
      return new Response(upstream.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'X-Accel-Buffering': 'no',
        },
      });
    }
  } catch {
    // fall through to fallback stream
  }

  // Fallback SSE stream — emits a status line every 3s until client disconnects
  const abortSignal = request.signal;
  let idx = 0;

  const stream = new ReadableStream({
    start(controller) {
      if (abortSignal.aborted) {
        controller.close();
        return;
      }

      const enc = new TextEncoder();

      const send = () => {
        if (abortSignal.aborted) return;
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { hour12: false });
        const msg = FALLBACK_LOGS[idx % FALLBACK_LOGS.length];
        idx++;
        const data = JSON.stringify({ time, message: msg });
        try {
          controller.enqueue(enc.encode(`data: ${data}\n\n`));
        } catch {
          // controller already closed — stop
          clearInterval(timer);
        }
      };

      send();
      const timer = setInterval(send, 3000);

      abortSignal.addEventListener('abort', () => {
        clearInterval(timer);
        try { controller.close(); } catch { /* already closed */ }
      }, { once: true });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'X-Accel-Buffering': 'no',
    },
  });
}
