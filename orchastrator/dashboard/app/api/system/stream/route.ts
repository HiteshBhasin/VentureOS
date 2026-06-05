import { NextRequest } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

//Fallback log lines shown when backend is offline
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
  console.log('=== Backend Stream Connection Debug ===');
  console.log('Backend URL:', BACKEND);
  console.log('Auth token present:', !!auth);
  console.log('Full endpoint:', `${BACKEND}/api/v1/system/stream`);
  // Try to proxy the real backend SSE stream
  try {
    const upstream = await fetch(`${BACKEND}/api/v1/system/stream`, {
      headers: { Authorization: auth },
      signal: AbortSignal.timeout(5000), // Increased from 3s to 5s to reduce reconnection thrashing
    });
    console.log('Response status:', upstream.status);
    console.log('Response ok:', upstream.ok);
    console.log('Response headers:', Object.fromEntries(upstream.headers.entries()));
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
  } catch(error) {
    console.error('❌ Connection failed:', error);
    console.error('Error details:', {
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      cause: error instanceof Error ? error.cause : undefined
    });
  }

  // Fallback SSE stream — emits a status line every 3s, max 10 times (30s total)
  const abortSignal = request.signal;
  let idx = 0;
  const MAX_FALLBACK_ITERATIONS = 10; // Prevent infinite loop

  const stream = new ReadableStream({
    start(controller) {
      if (abortSignal.aborted) {
        controller.close();
        return;
      }

      const enc = new TextEncoder();

      const send = () => {
        if (abortSignal.aborted || idx >= MAX_FALLBACK_ITERATIONS) {
          clearInterval(timer);
          controller.close();
          return;
        }
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
