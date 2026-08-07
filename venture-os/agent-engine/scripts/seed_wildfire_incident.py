"""
Seed a fake wildfire incident and kick off the emergency-coordination plan.

Inserts exactly one row into public.tasks — type='assess_route'. Once a
worker (worker.py) picks it up and completes it, _advance_emergency_plan()
inserts 'clear_zone', then 'dispatch', then 're_plan' automatically, each
carrying the previous step's result forward. All four share one goal_id.

Run from agent-engine/ (with the worker running in another terminal):
    python scripts/seed_wildfire_incident.py
"""

import os
import sys
import uuid
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]  # agent-engine/ (where .env lives)
sys.path.insert(0, str(ROOT))

load_dotenv(dotenv_path=ROOT / ".env")

# The fake incident — everything the first step needs to know. Real-portal
# scenarios (item 6) will replace this with data pulled from the Wildfire
# Portal instead of a hardcoded string.
INCIDENT = """
Wildfire near Ridgeview Canyon has jumped containment and is spreading
toward Ridgeview Estates (~340 residents). Highway 12, the primary
evacuation route, is blocked by a fallen power line near mile marker 4.
The secondary route via Old Mill Road is unconfirmed — it may pass close
to the active burn area. Available resources: 2 fire crews, 1 law
enforcement traffic-control unit, 3 evacuation buses. Wind is shifting
northeast at 15mph and is expected to reach the neighborhood within 90
minutes.
""".strip()

ASSESS_ROUTE_INSTRUCTIONS = """
Assess the safest available evacuation route out of Ridgeview Estates
given the incident above. Weigh the blocked primary route against the
unconfirmed secondary route. If cluster history is available, check it
for past incidents or route conditions in this area before deciding.
State which route you recommend, why, and what risks remain.
""".strip()


def _connect() -> psycopg2.extensions.connection:
    db_url = os.getenv("COCRAOCH_DB_URL")
    if not db_url:
        raise EnvironmentError("COCRAOCH_DB_URL is not set in .env")
    return psycopg2.connect(db_url)


def seed(user_id: str) -> None:
    goal_id = str(uuid.uuid4())
    description = f"[Incident]\n{INCIDENT}\n\n[Your task — assess_route]\n{ASSESS_ROUTE_INSTRUCTIONS}"

    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.tasks
                    (user_id, goal_id, title, description, type, priority, status)
                VALUES (%s, %s, %s, %s, 'assess_route', 'high', 'pending')
                RETURNING id;
                """,
                (user_id, goal_id, "Assess Route", description),
            )
            task_id = cur.fetchone()[0]
            conn.commit()
    finally:
        conn.close()

    print(f"Seeded emergency plan — goal_id={goal_id}")
    print(f"First task (assess_route) id={task_id}")
    print()
    print("Start the worker if it isn't already running:")
    print("    python worker.py")
    print()
    print("Watch progress with:")
    print(
        "    SELECT type, status, title FROM public.tasks "
        f"WHERE goal_id = '{goal_id}' ORDER BY created_at;"
    )


if __name__ == "__main__":
    # No user_id required by the schema (tasks.user_id has no FK constraint)
    # — pass one as an arg if you want to tie this to a real dashboard user,
    # otherwise a fresh UUID is fine for a standalone test.
    user_id = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())
    seed(user_id)
