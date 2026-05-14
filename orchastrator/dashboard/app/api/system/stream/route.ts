import { NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';

// Mock log lines cycling for when backend is offline
const MOCK_LOGS = [
  '[OK] COMMAND RECEIVED: INIT_MARKETING_STRAT_V2',
  '[PROC] ANALYZING OBJECTIVE...',
  '[PROC] DECOMPOSING GOAL: "SaaS Product Marketing"',
  '[SPAWN] SPAWNING ANALYST_NODE_04... SUCCESS',
  '[PROC] RETRIEVING COMPETITOR DATA VIA PERPLEXITY_ENGINE',
  '[OK] NODE_04: META STRATEGY GEN COMPONENT ACTIVE',
  '[...] AGGREGATING MARKET SEGMENTS_',
  '[PROC] CROSS-REFERENCING PRICING MODELS...',
  '[OK] PERSONA_MATRIX INITIALIZED',
  '[PROC] GENERATING AD COPY VARIANTS...',
];

export async function GET() {
  // Try to stream from backend first
  try {
    const upstream = await fetch(`${BACKEND}/api/v1/system/stream`, {
      signal: AbortSignal.timeout(3000),
    });
    if (upstream.ok && upstream.body) {
      return new Response(upstream.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'X-Accel-Buffering': 'no',
        },
      });
    }
  } catch {
    // fall through to mock stream
  }

  // Mock SSE stream — emits a log line every 2s
  let idx = 0;
  const stream = new ReadableStream({
    async start(controller) {
      const send = () => {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { hour12: false });
        const msg = MOCK_LOGS[idx % MOCK_LOGS.length];
        idx++;
        const data = JSON.stringify({ time, message: msg });
        controller.enqueue(new TextEncoder().encode(`data: ${data}\n\n`));
      };

      send(); // send one immediately
      const interval = setInterval(send, 2000);

      // Auto-close after 60s to avoid runaway connections
      setTimeout(() => {
        clearInterval(interval);
        controller.close();
      }, 60_000);
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
