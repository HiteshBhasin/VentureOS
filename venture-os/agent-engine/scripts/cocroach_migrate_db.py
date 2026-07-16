"""
Database migration — create all tables required by VentureOS agent-engine.

Tables created:
  - profiles      (mirrors cocroachDB auth.users for app-level data)
  - agents        (AI agents created by users)
  - tasks         (work items dispatched to agents)
  - memory_items  (agent memory / context entries)

Run from agent-engine/:
    python scripts/migrate_db.py

ALSO NEED A CONNECTION POOL SO THAT IT IS NOT ASKING FOR THE CONNECTION ON EVERY REQUEST.
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]  # agent-engine/ (where .env lives)

sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT / ".env")

logger = logging.getLogger(__name__)

import psycopg2

try:
    conn = psycopg2.connect(os.getenv("COCRAOCH_DB_URL"))
    if conn:
        logger.info("connection has been established", conn)
except Exception as e:
    logger.exception(f"cocroach connection: ", e)


MIGRATION = """
-- ─────────────────────────────────────────────────────────
-- Enable UUID extension (idempotent)
-- ─────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────
-- profiles
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────
-- agents
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.agents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    model           TEXT NOT NULL DEFAULT 'gpt-4',
    status          TEXT NOT NULL DEFAULT 'idle',
    activity        TEXT NOT NULL DEFAULT 'IDLE',
    progress        INTEGER NOT NULL DEFAULT 0,
    llm_config      JSONB NOT NULL DEFAULT '{}',
    memory_config   JSONB NOT NULL DEFAULT '{}',
    tool_config     JSONB NOT NULL DEFAULT '[]',
    tokens_per_sec  FLOAT NOT NULL DEFAULT 0.0,
    cost_estimate   FLOAT NOT NULL DEFAULT 0.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_user_id ON public.agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_type    ON public.agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status  ON public.agents(status);

-- ─────────────────────────────────────────────────────────
-- tasks
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.tasks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL,
    agent_id    UUID REFERENCES public.agents(id) ON DELETE SET NULL,
    goal_id     UUID,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    type        TEXT NOT NULL DEFAULT 'custom',
    status      TEXT NOT NULL DEFAULT 'pending',
    priority    TEXT NOT NULL DEFAULT 'medium',
    progress    INTEGER NOT NULL DEFAULT 0,
    tags        JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user_id  ON public.tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON public.tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status   ON public.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON public.tasks(priority);

-- ─────────────────────────────────────────────────────────
-- memory_items
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.memory_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL,
    agent_id    UUID REFERENCES public.agents(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,
    value       JSONB NOT NULL DEFAULT '{}',
    memory_type TEXT NOT NULL DEFAULT 'short_term',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_memory_user_id  ON public.memory_items(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_agent_id ON public.memory_items(agent_id);

-- ─────────────────────────────────────────────────────────
-- altering_task_table 
-- ─────────────────────────────────────────────────────────
ALTER TABLE public.tasks
  ADD COLUMN IF NOT EXISTS attempts     INTEGER      NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS visible_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS claimed_at   TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS result       JSONB,
  ADD COLUMN IF NOT EXISTS error        TEXT;

CREATE INDEX IF NOT EXISTS idx_tasks_queue
  ON public.tasks (status, visible_at);
"""


def connection() -> None:
    if conn:
        conn.autocommit = True
    try:
        with conn.cursor() as cur:
            print("running migration to Cocroach_db")
            cur.execute(MIGRATION)
        print("\nMigration complete. Tables created (or already existed):")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            )
            tables = [row[0] for row in cur.fetchall()]
            for t in tables:
                print(f"   - {t}")
    except Exception as e:
        logger.exception(
            " connection either didnt establish or established partially: ", e
        )
    finally:
        conn.close()


if __name__ == "__main__":
    connection()
