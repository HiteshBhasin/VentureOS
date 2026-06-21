"""
Background worker — poll the tasks table, claim and execute pending tasks.

Run independently alongside the FastAPI server:
    python worker.py

Environment variables required (same .env as the API):
    DATABASE_URL   — direct Postgres connection for atomic claim queries
    DEFAULT_LLM_MODEL — model to use (default: gpt-4)
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Allow imports from agent-engine root
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT.parents[1] / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 5       # how long to sleep when the queue is empty
LEASE_MINUTES = 10              # how long a worker holds a task before it can be reclaimed
MAX_ATTEMPTS = 3                # tasks are dead-lettered after this many failures
RETRY_BACKOFF_SECONDS = 30      # first retry delay; doubles each attempt (30s, 60s, 120s)

# ── SQL statements ────────────────────────────────────────────────────────────

# Atomically grab the highest-priority pending task whose lease has not started
# (or whose lease has expired — covers dead-worker recovery).
# FOR UPDATE SKIP LOCKED ensures two workers never claim the same row.
_CLAIM_SQL = f"""
UPDATE public.tasks
SET
    status     = 'running',
    claimed_at = NOW(),
    visible_at = NOW() + INTERVAL '{LEASE_MINUTES} minutes',
    attempts   = attempts + 1,
    updated_at = NOW()
WHERE id = (
    SELECT id FROM public.tasks
    WHERE status = 'pending'
      AND visible_at <= NOW()
    ORDER BY
        CASE priority
            WHEN 'critical' THEN 1
            WHEN 'high'     THEN 2
            WHEN 'medium'   THEN 3
            WHEN 'low'      THEN 4
            ELSE 5
        END ASC,
        created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
RETURNING id, title, description, user_id, priority, attempts;
"""

# Return stale 'running' tasks whose lease expired back to 'pending'
# so another worker (or the next poll) can reclaim them.
_RECLAIM_SQL = """
UPDATE public.tasks
SET
    status     = 'pending',
    visible_at = NOW(),
    updated_at = NOW()
WHERE status = 'running'
  AND visible_at < NOW()
  AND attempts < %s
RETURNING id;
"""

_COMPLETE_SQL = """
UPDATE public.tasks
SET status = 'completed', result = %s, progress = 100, updated_at = NOW()
WHERE id = %s;
"""

_FAIL_SQL = """
UPDATE public.tasks
SET status = %s, error = %s, visible_at = %s, updated_at = NOW()
WHERE id = %s;
"""


# ── Database helpers ──────────────────────────────────────────────────────────

def _connect() -> psycopg2.extensions.connection:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise EnvironmentError("DATABASE_URL is not set in .env")
    return psycopg2.connect(db_url)


def _claim_task(conn) -> dict | None:
    """Atomically claim one pending task. Returns the row dict or None."""
    with conn.cursor() as cur:
        cur.execute(_CLAIM_SQL)
        row = cur.fetchone()
        conn.commit()
    if not row:
        return None
    return {
        "id":          str(row[0]),
        "title":       row[1],
        "description": row[2] or "",
        "user_id":     str(row[3]),
        "priority":    row[4],
        "attempts":    row[5],
    }


def _reclaim_dead(conn) -> int:
    """Return stuck tasks (dead workers) back to pending. Returns count reclaimed."""
    with conn.cursor() as cur:
        cur.execute(_RECLAIM_SQL, (MAX_ATTEMPTS,))
        reclaimed = cur.fetchall()
        conn.commit()
    return len(reclaimed)


def _mark_completed(conn, task_id: str, result: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(_COMPLETE_SQL, (psycopg2.extras.Json(result), task_id))
        conn.commit()


def _mark_failed(conn, task_id: str, error: str, attempts: int) -> None:
    if attempts >= MAX_ATTEMPTS:
        # Dead-letter — no more retries
        status = "failed"
        visible_at = "NOW()"
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE public.tasks SET status='failed', error=%s, updated_at=NOW() WHERE id=%s",
                (error, task_id),
            )
            conn.commit()
    else:
        # Exponential backoff: 30s, 60s, 120s …
        backoff = RETRY_BACKOFF_SECONDS * (2 ** (attempts - 1))
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.tasks
                SET status='pending', error=%s,
                    visible_at = NOW() + (%s || ' seconds')::INTERVAL,
                    updated_at = NOW()
                WHERE id=%s
                """,
                (error, str(backoff), task_id),
            )
            conn.commit()
        logger.info(f"Task {task_id} requeued — retrying in {backoff}s (attempt {attempts}/{MAX_ATTEMPTS})")


# ── Main worker loop ──────────────────────────────────────────────────────────

def run() -> None:
    from core.llm_class import LLM
    from core.orchestrator import Orchestrator

    model = os.getenv("DEFAULT_LLM_MODEL", "gpt-4")
    logger.info(f"Worker starting — model={model}, poll_interval={POLL_INTERVAL_SECONDS}s")

    llm = LLM(model=model)
    conn = _connect()
    logger.info("Database connection established")

    while True:
        try:
            # ── Recover any tasks whose lease expired (dead workers) ──
            reclaimed = _reclaim_dead(conn)
            if reclaimed:
                logger.info(f"Reclaimed {reclaimed} stuck task(s) back to pending")

            # ── Try to claim the next highest-priority task ──
            task = _claim_task(conn)
            if not task:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            logger.info(
                f"Claimed task {task['id']} "
                f"(priority={task['priority']}, attempt={task['attempts']}/{MAX_ATTEMPTS})"
            )

            # ── Run the orchestrator ──
            try:
                orchestrator = Orchestrator(llm=llm)
                user_input = f"{task['title']}: {task['description']}".strip(": ")
                result = orchestrator.process_user_request(user_input)
                _mark_completed(conn, task["id"], result)
                logger.info(f"Task {task['id']} completed successfully")

            except Exception as exc:
                logger.error(f"Task {task['id']} failed: {exc}", exc_info=True)
                _mark_failed(conn, task["id"], str(exc), task["attempts"])

        except psycopg2.OperationalError as exc:
            # Lost DB connection — reconnect and keep going
            logger.warning(f"DB connection lost ({exc}), reconnecting in 5s...")
            try:
                conn.close()
            except Exception:
                pass
            time.sleep(5)
            try:
                conn = _connect()
                logger.info("Reconnected to database")
            except Exception as reconnect_exc:
                logger.error(f"Reconnect failed: {reconnect_exc}")

        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break

        except Exception as exc:
            logger.error(f"Unexpected worker error: {exc}", exc_info=True)
            time.sleep(POLL_INTERVAL_SECONDS)

    try:
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    run()