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

load_dotenv(dotenv_path=ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 5  # how long to sleep when the queue is empty
LEASE_MINUTES = 10  # how long a worker holds a task before it can be reclaimed
MAX_ATTEMPTS = 3  # tasks are dead-lettered after this many failures
RETRY_BACKOFF_SECONDS = 30  # first retry delay; doubles each attempt (30s, 60s, 120s)
SPAWNED_AGENT_CLEANUP_INTERVAL_SECONDS = (
    3600  # how often to sweep spawned_agents/ for stale files
)
TASK_TIMEOUT_HOURS = float(os.getenv("TASK_TIMEOUT_HOURS", "24"))  # dead-letter SLA
DEADLETTER_SWEEP_INTERVAL_SECONDS = 300  # how often to check for tasks past the SLA

# ── SQL statements ────────────────────────────────────────────────────────────

# Atomically grab the highest-priority pending task whose lease has not started
# (or whose lease has expired — covers dead-worker recovery).
# FOR UPDATE SKIP LOCKED ensures two workers never claim the same row.
# _CLAIM_SQL = f"""
# UPDATE public.tasks
# SET
#     status     = 'running',
#     claimed_at = NOW(),
#     visible_at = NOW() + INTERVAL '{LEASE_MINUTES} minutes',
#     attempts   = attempts + 1,
#     updated_at = NOW()
# WHERE id = (
#     SELECT id FROM public.tasks
#     WHERE status = 'pending'
#       AND visible_at <= NOW()
#     ORDER BY
#         CASE priority
#             WHEN 'high'     THEN 1
#             WHEN 'medium'   THEN 2
#             WHEN 'low'      THEN 3
#             ELSE 4
#         END ASC,
#         created_at ASC
#     LIMIT 1
#     FOR UPDATE SKIP LOCKED
# )
# RETURNING id, title, description, user_id, priority, attempts, agent_id;
# """
_CLAIM_SQL = """
UPDATE public.tasks
SET
    status     = 'running',
    claimed_at = now(),
    visible_at = now() + $2::INTERVAL,
    attempts   = attempts + 1,
    updated_at = now()
WHERE id = (
    SELECT id FROM public.tasks
    WHERE bucket = $1
      AND status = 'pending'
      AND visible_at <= now()
    ORDER BY priority_rank ASC, visible_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
AND status = 'pending'
RETURNING id, title, description, user_id, agent_id,
          priority, attempts, idempotency_key;
"""

# The REAPER


_THE_REAPER = """

UPDATE public.tasks
SET 
    status     = 'pending',
    claimed_at = NULL,
    visible_at = now(),
    attempts   = attempts + 1,
    updated_at = now()
WHERE id IN (
    SELECT id 
    FROM public.tasks
    WHERE status='running' 
    AND visible_at <= now()
    LIMIT 100
    FOR UPDATE SKIP LOCKED
)
"""
_RETIRED_TASKS = """
UPDATE public.tasks
SET
    status = "failed",
    error  = "exceeded max attempts",
    updated_at = now()
WHERE status = "running"
    AND visible_at <=nows()
    AND attempts>=$1
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
SET status = 'completed', result = %s, error = NULL, progress = 100, updated_at = NOW()
WHERE id = %s;
"""

_FAIL_SQL = """
UPDATE public.tasks
SET status = %s, error = %s, visible_at = %s, updated_at = NOW()
WHERE id = %s;
"""

# Dead-letter any task that has sat in pending/running past the SLA, regardless
# of attempts remaining — a 24h-old task is stale even if it still has retries.
_DEADLETTER_SQL = """
UPDATE public.tasks
SET status = 'failed', error = %s, updated_at = NOW()
WHERE status IN ('pending', 'running')
  AND created_at < NOW() - (%s || ' hours')::INTERVAL
RETURNING id;
"""

# Reflect real task execution onto the DB agents table so the dashboard's
# Agents page shows something other than permanently-idle placeholder rows.
_AGENT_SET_ACTIVE_SQL = """
UPDATE public.agents
SET status = 'active', activity = %s, updated_at = NOW()
WHERE id = %s;
"""

_AGENT_SET_IDLE_SQL = """
UPDATE public.agents
SET status = 'idle', activity = 'IDLE', progress = 0, updated_at = NOW()
WHERE id = %s;
"""

# For tasks created without an explicit agent_id (e.g. the dashboard's
# objective bar), atomically claim one idle agent belonging to the same user
# so the Agents page reflects real work instead of sitting permanently idle.
_ASSIGN_IDLE_AGENT_SQL = """
UPDATE public.agents
SET status = 'active', activity = %s, updated_at = NOW()
WHERE id = (
    SELECT id FROM public.agents
    WHERE user_id = %s AND status = 'idle'
    ORDER BY updated_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
RETURNING id;
"""


# ── Database helpers ──────────────────────────────────────────────────────────
NUM_BUCKETS = 16
LEASE = 2  # default
import asyncio, random
import asyncpg


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
        "id": str(row[0]),
        "title": row[1],
        "description": row[2] or "",
        "user_id": str(row[3]),
        "priority": row[4],
        "attempts": row[5],
        "agent_id": str(row[6]) if row[6] else None,
    }


async def claim_oneTask(conn, buckets, retries=5):
    for i in range(retries):
        try:
            with conn.acquire() as cur:
                result = await cur.fetchall(_CLAIM_SQL, buckets, retries)
                return result
        except asyncpg.PostgresError as e:
            if getattr(e, "sqlstate", None) != "40001":
                raise
            await asyncio.sleep((0.05 * 2**i) + random.uniform(0, 0.05))
    return None


async def clain_anyTask(conn, worker_id):
    start = worker_id % NUM_BUCKETS

    for i in range(NUM_BUCKETS):
        buckets = (start + i) % NUM_BUCKETS
        row = await claim_oneTask(conn, buckets=buckets)
        if row:
            return
    return None


async def reaper(conn, interval=30, max_attemps=5):
    try:
        with conn.acquire() as cur:
            await cur.execute(_THE_REAPER, max_attemps)
            await cur.execute(_RETIRED_TASKS, max_attemps)
    except:
        raise
    await asyncio.sleep(interval)


def _reclaim_dead(conn) -> int:
    """Return stuck tasks (dead workers) back to pending. Returns count reclaimed."""
    with conn.cursor() as cur:
        cur.execute(_RECLAIM_SQL, (MAX_ATTEMPTS,))
        reclaimed = cur.fetchall()
        conn.commit()
    return len(reclaimed)


def _deadletter_stale(conn, timeout_hours: float) -> int:
    """Fail any task that has been pending/running longer than the SLA.
    Returns count dead-lettered."""
    error = f"Timed out — exceeded {timeout_hours:g}h SLA without completing"
    with conn.cursor() as cur:
        cur.execute(_DEADLETTER_SQL, (error, str(timeout_hours)))
        deadlettered = cur.fetchall()
        conn.commit()
    return len(deadlettered)


def _set_agent_active(conn, agent_id: str, activity: str) -> None:
    """Best-effort — a bad/missing agent_id shouldn't abort task execution."""
    try:
        with conn.cursor() as cur:
            cur.execute(_AGENT_SET_ACTIVE_SQL, (activity, agent_id))
            conn.commit()
    except Exception as exc:
        logger.warning(f"Could not mark agent {agent_id} active: {exc}")
        conn.rollback()


def _set_agent_idle(conn, agent_id: str) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(_AGENT_SET_IDLE_SQL, (agent_id,))
            conn.commit()
    except Exception as exc:
        logger.warning(f"Could not mark agent {agent_id} idle: {exc}")
        conn.rollback()


def _assign_idle_agent(conn, user_id: str, activity: str) -> str | None:
    """Claim one idle agent for this user. Returns its id, or None if the
    user has no agent rows (or none are idle) — task execution proceeds
    either way, this is purely for dashboard visibility."""
    try:
        with conn.cursor() as cur:
            cur.execute(_ASSIGN_IDLE_AGENT_SQL, (activity, user_id))
            row = cur.fetchone()
            conn.commit()
        return str(row[0]) if row else None
    except Exception as exc:
        logger.warning(f"Could not auto-assign an idle agent for user {user_id}: {exc}")
        conn.rollback()
        return None


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
        logger.info(
            f"Task {task_id} requeued — retrying in {backoff}s (attempt {attempts}/{MAX_ATTEMPTS})"
        )


# ── Main worker loop ──────────────────────────────────────────────────────────


def run() -> None:
    from core.llm_class import LLM
    from core.orchestrator import Orchestrator
    from core.agent_factory import cleanup_stale_spawned_agents

    model = os.getenv("DEFAULT_LLM_MODEL", "gpt-4")
    logger.info(
        f"Worker starting — model={model}, poll_interval={POLL_INTERVAL_SECONDS}s"
    )

    llm = LLM(model=model)
    conn = _connect()
    logger.info("Database connection established")

    removed = cleanup_stale_spawned_agents()
    if removed:
        logger.info(f"Startup cleanup: removed {removed} stale spawned-agent file(s)")
    last_cleanup_at = time.time()
    last_deadletter_at = time.time()

    while True:
        try:
            if time.time() - last_cleanup_at > SPAWNED_AGENT_CLEANUP_INTERVAL_SECONDS:
                cleanup_stale_spawned_agents()
                last_cleanup_at = time.time()

            if time.time() - last_deadletter_at > DEADLETTER_SWEEP_INTERVAL_SECONDS:
                deadlettered = _deadletter_stale(conn, TASK_TIMEOUT_HOURS)
                if deadlettered:
                    logger.warning(
                        f"Dead-lettered {deadlettered} task(s) past the "
                        f"{TASK_TIMEOUT_HOURS:g}h SLA"
                    )
                last_deadletter_at = time.time()

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

            agent_id = task["agent_id"]
            if agent_id:
                _set_agent_active(conn, agent_id, "RUNNING")
            else:
                agent_id = _assign_idle_agent(conn, task["user_id"], "RUNNING")
                if agent_id:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE public.tasks SET agent_id = %s WHERE id = %s",
                            (agent_id, task["id"]),
                        )
                        conn.commit()
                    logger.info(f"Auto-assigned agent {agent_id} to task {task['id']}")

            # ── Run the orchestrator ──
            try:
                orchestrator = Orchestrator(llm=llm)
                user_input = f"{task['title']}: {task['description']}".strip(": ")
                result = orchestrator.process_user_request(user_input)
                # process_user_request() swallows its own exceptions and returns
                # {"status": "error", ...} instead of raising — treat that the
                # same as a raised exception, or every orchestrator-level failure
                # would be recorded as "completed".
                if result.get("status") == "error":
                    raise RuntimeError(
                        result.get("message", "Orchestrator returned an error")
                    )
                _mark_completed(conn, task["id"], result)
                logger.info(f"Task {task['id']} completed successfully")

            except Exception as exc:
                logger.error(f"Task {task['id']} failed: {exc}", exc_info=True)
                _mark_failed(conn, task["id"], str(exc), task["attempts"])

            finally:
                if agent_id:
                    _set_agent_idle(conn, agent_id)

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
