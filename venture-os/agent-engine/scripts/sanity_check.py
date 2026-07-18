#!/usr/bin/env python3
"""
Sanity check: Insert 500 fake tasks and verify even distribution across 16 buckets.

This is a 30-second verification that:
  1. The database cluster exists and is reachable
  2. The tasks table exists
  3. The bucket hashing is working correctly
  4. Task distribution across buckets is roughly even

Run from agent-engine/:
    python scripts/sanity_check.py

Requires:
    - PostgreSQL/CockroachDB with DATABASE_URL set
    - .env file with DATABASE_URL, or environment variable
"""

import os
import sys
import time
import uuid
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]  # agent-engine/
print(ROOT)
sys.path.insert(0, str(ROOT))

# Try to load .env if it exists
env_file = ROOT / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    print(f"Note: {env_file} does not exist, using environment variables\n")


def connect():
    # Try multiple sources for DATABASE_URL
    db_url = os.getenv("COCRAOCH_DB_URL")

    if not db_url:
        print("ERROR: No database URL found!")
        print("\nSet one of these environment variables:")
        print("  - DATABASE_URL")
        print("  - COCRAOCH_DB_URL")
        print("  - POSTGRES_URL")
        print(
            "\nOr create a .env file in agent-engine/ with: DATABASE_URL=postgresql://...\n"
        )
        raise EnvironmentError("No database connection URL available")

    return psycopg2.connect(db_url)


def sanity_check():
    print("\n" + "=" * 70)
    print("  SANITY CHECK: Task Distribution Across 16 Buckets")
    print("=" * 70 + "\n")

    try:
        conn = connect()
        cur = conn.cursor()
        print("✓ Connected to database\n")

        # ── Step 1: Verify tables exist ───────────────────────────────────────
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'tasks'
            """)
        if not cur.fetchone():
            print("✗ FAIL: tasks table does not exist")
            return False

        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'tasks' AND column_name = 'bucket'
            """)
        if not cur.fetchone():
            print("✗ FAIL: bucket column does not exist on tasks table")
            return False

        print("✓ Tables and bucket column exist\n")

        # ── Step 2: Insert 500 fake tasks ─────────────────────────────────────
        print("Inserting 500 fake tasks...")
        start_time = time.time()

        # Use a test user_id for isolation
        test_user_id = str(uuid.uuid4())

        # Build INSERT with 500 rows
        insert_sql = """
        INSERT INTO public.tasks (id, user_id, title, description, type, status)
        VALUES
        """

        values = []
        for i in range(500):
            task_id = str(uuid.uuid4())
            values.append(
                f"('{task_id}', '{test_user_id}', 'Fake Task {i}', 'Test task for sanity check', 'custom', 'pending')"
            )

        insert_sql += ",\n        ".join(values)
        insert_sql += "\n        ON CONFLICT (id) DO NOTHING;"

        cur.execute(insert_sql)
        conn.commit()
        insert_time = time.time() - start_time

        print(f"✓ Inserted 500 tasks in {insert_time:.2f}s\n")

        # ── Step 3: Count tasks per bucket ────────────────────────────────────
        print("Counting tasks per bucket...\n")

        cur.execute(
            """
            SELECT bucket, COUNT(*) as count
            FROM public.tasks
            WHERE user_id = %s
            GROUP BY bucket
            ORDER BY bucket ASC
            """,
            (test_user_id,),
        )

        results = cur.fetchall()
        bucket_counts = {i: 0 for i in range(16)}

        for bucket, count in results:
            bucket_counts[bucket] = count

        # ── Step 4: Display distribution ──────────────────────────────────────
        print("Bucket Distribution (target: ~31-32 per bucket)")
        print("-" * 50)

        total = sum(bucket_counts.values())
        expected_per_bucket = total / 16

        for bucket in range(16):
            count = bucket_counts[bucket]
            pct = (count / total * 100) if total > 0 else 0

            # Visual bar chart
            bar_width = int(count / 2)  # Scale for visibility
            bar = "█" * bar_width

            # Flag if distribution is off (> 10% deviation)
            deviation = abs(count - expected_per_bucket) / expected_per_bucket * 100
            status = "✓" if deviation < 10 else "⚠" if deviation < 20 else "✗"

            print(
                f"  {status} Bucket {bucket:2d}: {count:3d} tasks ({pct:5.1f}%) {bar}"
            )

        print("-" * 50)
        print(f"Total: {total} tasks\n")

        # ── Step 5: Verdict ───────────────────────────────────────────────────
        deviations = []
        for count in bucket_counts.values():
            if count > 0:
                deviation = abs(count - expected_per_bucket) / expected_per_bucket * 100
                deviations.append(deviation)

        max_deviation = max(deviations) if deviations else 0
        avg_deviation = sum(deviations) / len(deviations) if deviations else 0

        print(f"Max deviation:  {max_deviation:.1f}%")
        print(f"Avg deviation:  {avg_deviation:.1f}%\n")

        if max_deviation < 15:
            print("✓ PASS: Hash distribution is sound!")
            print("  → Cluster exists")
            print("  → Tables exist")
            print("  → Buckets spread evenly")
            print("  → Ready to build workers on this foundation\n")
            result = True
        elif max_deviation < 25:
            print("⚠ WARNING: Distribution is uneven, but within tolerance")
            print("  → May want to review hashing function\n")
            result = True
        else:
            print("✗ FAIL: Hash distribution is broken!")
            print("  → Do not proceed until hashing is fixed\n")
            result = False

        # ── Cleanup ───────────────────────────────────────────────────────────
        print("Cleaning up test data...")
        cur.execute(
            "DELETE FROM public.tasks WHERE user_id = %s",
            (test_user_id,),
        )
        conn.commit()
        print("✓ Test data removed\n")

        cur.close()
        conn.close()

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = sanity_check()
    sys.exit(0 if success else 1)
