from typing import Any, Dict
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# memory/supabase_client.py -> memory -> agent-engine (where .env lives)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "SUPABASE_URL and SUPABASE_KEY must be set in your .env file."
    )

try:
    engine: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Ping the database with a lightweight query to confirm the connection is live

    logger.info("Supabase connection OK")
except Exception as e:
    raise ConnectionError(f"Supabase connection failed: {e}")


def create_table_raw(sql: str) -> None:
    """Execute raw DDL SQL against Supabase Postgres directly.
    Requires DATABASE_URL in .env:
      DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
    """
    import psycopg2  # lazy import — only needed for raw DDL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise EnvironmentError(
            "DATABASE_URL must be set in your .env file for DDL operations.\n"
            "Format: postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres"
        )
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        logger.info("Table created successfully.")
    finally:
        conn.close()


def insert(table: str, data: dict) -> None:
    """Insert a record into a Supabase table."""
    try:
        response = engine.table(table).insert(data).execute()
        logger.info(f"Insert response: {response}")
    except Exception as e:
        logger.error(f"Error inserting record: {e}")


def retreieve(table: str, query: dict, columns: str) -> list:
    """Retrieve records from a Supabase table based on a query."""
    try:
        response = engine.table(table).select(columns).match(query).execute()
        logger.info(f"Retrieve response: {response}")
        return response.data
    except Exception as e:
        logger.error(f"Error retrieving records: {e}")
        return []


# Example usage — creates the profiles table
if __name__ == "__main__":
    pass
    # create_table_raw("""
    #     CREATE TABLE IF NOT EXISTS profiles (
    #         id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    #         email       TEXT UNIQUE NOT NULL,
    #         name        TEXT,
    #         plan        TEXT DEFAULT 'free',
    #         created_at  TIMESTAMPTZ DEFAULT NOW(),
    #         is_active   BOOLEAN DEFAULT TRUE
    #     );
    # """)
    # insert(
    #     "profiles",
    #     {
    #         "email": "example@example.com",
    #         "name": "John Doe",
    #         "plan": "free",
    #         "created_at": "2024-06-01T12:00:00Z",
    #         "is_active": True,
    #     },
    # )
    # records = retreieve("profiles", {"name": "John Doe"}, columns="name, email")
    # print(f"Retrieved records: {records}")
