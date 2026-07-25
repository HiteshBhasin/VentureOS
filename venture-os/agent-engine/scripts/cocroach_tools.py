"""
CockroachDB tools — Bedrock embeddings + memory_items read/write helpers.

Requires public.memory_items (see scripts/cocroach_migrate_db.py) with an
`embedding VECTOR(1024)` column.

Run from agent-engine/:
    python scripts/cocroach_tools.py
"""

import psycopg2
import os
import sys
import boto3
import json
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]  # agent-engine/ (where .env lives)

sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT / ".env")

logger = logging.getLogger(__name__)

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIM = 1024


def bedrock_embedding(text: str) -> list:
    """Embed `text` with Amazon Titan Embed Text v2. Returns a 1024-dim list of floats."""
    body = json.dumps(
        {"inputText": text, "dimensions": EMBEDDING_DIM, "normalize": True}
    )
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=EMBEDDING_MODEL_ID,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response["body"].read())
    return response_body.get("embedding", [])


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
    embedding = bedrock_embedding(text)
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
    embedding = _vector_literal(bedrock_embedding(query_text))
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
    vec = bedrock_embedding("connection smoke test")
    print(f"Bedrock OK — embedding dimension: {len(vec)}")

    conn = get_connection()
    print("CockroachDB connection OK")
    conn.close()
