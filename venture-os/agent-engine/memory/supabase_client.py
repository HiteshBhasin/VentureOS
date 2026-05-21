from supabase import create_client, Client
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")

try:
    engine: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Ping the database with a lightweight query to confirm the connection is live
    
    print("Supabase connection OK", engine)
except Exception as e:
    raise ConnectionError(f"Supabase connection failed: {e}")


def create_table_raw(sql: str) -> None:
    """Execute raw DDL SQL against Supabase Postgres directly.
    Requires DATABASE_URL in .env:
      DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise EnvironmentError("DATABASE_URL must be set in your .env file for DDL operations.")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Table created successfully.")
    finally:
        conn.close()


# Example usage — creates the profiles table
if __name__ == "__main__":
    create_table_raw("""
        CREATE TABLE IF NOT EXISTS profiles (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email       TEXT UNIQUE NOT NULL,
            name        TEXT,
            plan        TEXT DEFAULT 'free',
            created_at  TIMESTAMPTZ DEFAULT NOW(),
            is_active   BOOLEAN DEFAULT TRUE
        );
    """)
