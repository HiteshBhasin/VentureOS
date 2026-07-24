import psycopg2
import os
import sys
import boto3
import json
from pathlib import Path
import logging
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]  # agent-engine/ (where .env lives)

sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT / ".env")

logger = logging.getLogger(__name__)

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")


def bedrock_embedding(text: str) -> list:
    body = json.dumps({"input text": text, "dimension": 1024, "normalize": True})
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId="amazon-titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json",
    )
    if isinstance(response, dict):
        if response != None:
            response_body = json.loads(response.get("body", "{}"))
            return json.loads(response_body.get("body", "[]")).get("embedding", [])
    return []


def connection():
    conn = None

    try:
        conn = psycopg2.connect(os.getenv("COCRAOCH_DB_URL"))
        if conn:
            logger.info("connection has been established", conn)
    except Exception as e:
        logger.exception(f"cocroach connection: ", e)
        conn = None

    if conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            print("running migration to Cocroach_db")
            cur.execute(MIGRATION)
            print("\nMigration complete. Tables created (or already existed):")
    ...


def cocraoch_mcp():
    pass
