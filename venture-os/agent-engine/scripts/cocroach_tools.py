"""
CockroachDB tools — embeddings + memory_items read/write helpers.

Embeddings use Mistral (mistral-embed) rather than Bedrock Titan — this
account's Bedrock model access request wasn't approved, and mistral-embed
supports the same 1024-dim output via `output_dimension` with no access
request needed. Switch providers here only; the DB schema/queries are
unaffected either way.

Requires public.memory_items (see scripts/cocroach_migrate_db.py) with an
`embedding VECTOR(1024)` column.

Run from agent-engine/:
    python scripts/cocroach_tools.py
"""

import psycopg2
import os
import sys
import json
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv
from mistralai import Mistral

ROOT = Path(__file__).resolve().parents[1]  # agent-engine/ (where .env lives)

sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT / ".env")

logger = logging.getLogger(__name__)

_mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

EMBEDDING_MODEL_ID = "mistral-embed"
EMBEDDING_DIM = 1024


def embed_text(text: str) -> list:
    """Embed `text` with Mistral. Returns a 1024-dim list of floats."""
    response = _mistral_client.embeddings.create(
        model=EMBEDDING_MODEL_ID,
        inputs=[text],
        output_dimension=EMBEDDING_DIM,
    )
    embedding = response.data[0].embedding
    if not embedding:
        raise RuntimeError("Mistral embeddings call returned no vector")
    return embedding


def _vector_literal(embedding: list) -> str:
    """Format a Python list as a CockroachDB VECTOR input literal, e.g. '[0.1,0.2]'."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def get_connection():
    """Open a new CockroachDB connection. Caller is responsible for closing it."""
    db_url = os.getenv("COCRAOCH_DB_URL")
    if not db_url:
        raise EnvironmentError("COCRAOCH_DB_URL is not set (check agent-engine/.env)")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn


def store_memory(
    user_id: str,
    agent_id: str,
    key: str,
    value: dict,
    text: str,
    memory_type: str = "semantic",
) -> str:
    """Embed `text` and insert it into memory_items. Returns the new row's id."""
    embedding = embed_text(text)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.memory_items
                    (user_id, agent_id, key, value, embedding, memory_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_id,
                    agent_id,
                    key,
                    json.dumps(value),
                    _vector_literal(embedding),
                    memory_type,
                ),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT ... RETURNING id returned no row")
            return row[0]
    finally:
        conn.close()


def search_memory(
    query_text: str, agent_id: Optional[str] = None, top_k: int = 10
) -> list:
    """Semantic search over memory_items, nearest to `query_text` by cosine distance."""
    embedding = _vector_literal(embed_text(query_text))
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            where_clause = "WHERE agent_id = %s" if agent_id else ""
            params = (embedding,) + ((agent_id,) if agent_id else ()) + (top_k,)
            cur.execute(
                f"""
                SELECT id, key, value, memory_type, created_at,
                       embedding <=> %s AS distance
                FROM public.memory_items
                {where_clause}
                ORDER BY distance ASC
                LIMIT %s
                """,
                params,
            )
            columns = [desc[0] for desc in cur.description or []]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


if __name__ == "__main__":
    vec = embed_text("connection smoke test")
    print(f"Mistral embeddings OK — dimension: {len(vec)}")

    conn = get_connection()
    print("CockroachDB connection OK")
    conn.close()
