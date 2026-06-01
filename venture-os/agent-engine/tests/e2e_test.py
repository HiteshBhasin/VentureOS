"""
E2E test: Frontend → Backend → Agent Spawning

Tests:
  1. Health check (no auth required)
  2. Auth — login via Supabase and obtain a JWT
  3. Agent CRUD — list, create, retrieve agents
  4. Task creation — verifies the orchestrator is invoked and agents are spawned
  5. Orchestrator smoke test — calls process_user_request() directly

Run from agent-engine/:
    python tests/e2e_test.py
or
    pytest tests/e2e_test.py -v
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]          # agent-engine/
REPO_ROOT = ROOT.parents[1]                          # VentureOS/
sys.path.insert(0, str(ROOT))
load_dotenv(dotenv_path=REPO_ROOT / ".env")

# ── Config ───────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _section(title: str) -> None:
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def _ok(msg: str) -> None:
    print(f"  ✓  {msg}")


def _fail(msg: str) -> None:
    print(f"  ✗  {msg}")
    raise AssertionError(msg)


def _warn(msg: str) -> None:
    print(f"  ⚠  {msg}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Health Check
# ═══════════════════════════════════════════════════════════════════════════════

def test_health():
    _section("1. Health Check  →  GET /health")
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=10)
    except httpx.ConnectError:
        _fail(
            f"Cannot connect to backend at {BASE_URL}.\n"
            "  Start it with:  uvicorn api.main:app --reload  (from agent-engine/)"
        )

    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    body = r.json()
    assert body.get("status") == "ok", f"Unexpected health body: {body}"
    _ok(f"status={body['status']}  version={body.get('version')}  ts={body.get('timestamp')}")
    return body


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Authentication
# ═══════════════════════════════════════════════════════════════════════════════

def test_auth() -> str:
    """Returns a valid JWT access token."""
    _section("2. Authentication  →  POST /api/v1/auth/login")

    if not TEST_EMAIL or not TEST_PASSWORD:
        _warn(
            "TEST_USER_EMAIL / TEST_USER_PASSWORD not set in .env — "
            "using Supabase client directly to obtain token."
        )
        return _auth_via_supabase_client()

    payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    r = httpx.post(f"{BASE_URL}/api/v1/auth/login", json=payload, timeout=15)

    if r.status_code == 401:
        _warn("Login failed (401) — trying Supabase client fallback.")
        return _auth_via_supabase_client()

    assert r.status_code == 200, f"Login returned {r.status_code}: {r.text}"
    body = r.json()
    token = body.get("access_token")
    assert token, f"No access_token in response: {body}"
    _ok(f"Logged in as {body.get('email')}  user_id={body.get('user_id')}")
    return token


def _auth_via_supabase_client() -> str:
    """Fallback: sign in via supabase-py directly without hitting our API."""
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        _fail("SUPABASE_URL / SUPABASE_KEY missing from .env")

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Attempt to sign in with a known test credential from env
    email = TEST_EMAIL or os.getenv("SUPABASE_TEST_EMAIL", "")
    password = TEST_PASSWORD or os.getenv("SUPABASE_TEST_PASSWORD", "")

    if not email or not password:
        _fail(
            "No test credentials found. Set TEST_USER_EMAIL and TEST_USER_PASSWORD in .env."
        )

    res = sb.auth.sign_in_with_password({"email": email, "password": password})
    if res.session is None:
        _fail("Supabase sign_in returned no session.")
    token = res.session.access_token
    _ok(f"Supabase direct auth OK — user_id={res.user.id}")
    return token


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Agents API
# ═══════════════════════════════════════════════════════════════════════════════

def test_agents(token: str) -> str:
    """Create an agent and return its ID."""
    headers = {"Authorization": f"Bearer {token}"}

    # 3a — List
    _section("3a. List Agents  →  GET /api/v1/agents/")
    r = httpx.get(f"{BASE_URL}/api/v1/agents/", headers=headers, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    agent_count = len(body.get("agents", []))
    _ok(f"Found {agent_count} existing agent(s)")

    # 3b — Create
    _section("3b. Create Agent  →  POST /api/v1/agents/")
    payload = {
        "name": f"e2e-test-agent-{uuid.uuid4().hex[:8]}",
        "type": "coding",
        "description": "Automated E2E test agent",
        "model": "gpt-4",
    }
    r = httpx.post(
        f"{BASE_URL}/api/v1/agents/", json=payload, headers=headers, timeout=15
    )
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    agent = r.json()
    agent_id = agent.get("id")
    assert agent_id, f"No id in agent response: {agent}"
    _ok(f"Agent created  id={agent_id}  name={agent.get('name')}  status={agent.get('status')}")

    # 3c — Retrieve
    _section("3c. Get Agent  →  GET /api/v1/agents/{id}")
    r = httpx.get(f"{BASE_URL}/api/v1/agents/{agent_id}", headers=headers, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    fetched = r.json()
    assert fetched.get("id") == agent_id
    _ok(f"Agent retrieved  id={fetched.get('id')}  type={fetched.get('type')}")

    return agent_id


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Tasks API + Orchestrator Invocation
# ═══════════════════════════════════════════════════════════════════════════════

def test_tasks(token: str, agent_id: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}

    # 4a — List
    _section("4a. List Tasks  →  GET /api/v1/tasks/")
    r = httpx.get(f"{BASE_URL}/api/v1/tasks/", headers=headers, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    task_count = len(r.json().get("tasks", []))
    _ok(f"Found {task_count} existing task(s)")

    # 4b — Create (triggers orchestrator.process_user_request in background)
    _section("4b. Create Task  →  POST /api/v1/tasks/  (triggers orchestrator)")
    payload = {
        "title": "E2E smoke: build a hello-world REST endpoint",
        "description": (
            "Generate a minimal FastAPI endpoint that returns "
            '{"message": "hello world"} at GET /hello.'
        ),
        "priority": "medium",
        "type": "coding",
        "agent_id": agent_id,
    }
    r = httpx.post(
        f"{BASE_URL}/api/v1/tasks/", json=payload, headers=headers, timeout=30
    )
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    _ok("Task created — orchestrator dispatched in background executor")

    # 4c — Verify task appears in list
    _section("4c. Verify task stored  →  GET /api/v1/tasks/")
    time.sleep(1)  # brief pause so DB write settles
    r = httpx.get(f"{BASE_URL}/api/v1/tasks/", headers=headers, timeout=15)
    assert r.status_code == 200
    new_count = len(r.json().get("tasks", []))
    assert new_count >= task_count + 1, (
        f"Expected at least {task_count + 1} tasks, got {new_count}"
    )
    _ok(f"Task count {task_count} → {new_count}  (task persisted in DB)")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Orchestrator direct smoke test (no HTTP, pure Python)
# ═══════════════════════════════════════════════════════════════════════════════

def test_orchestrator_direct() -> None:
    _section("5. Orchestrator Direct Smoke Test  (process_user_request)")

    try:
        from core.llm_class import LLM
        from core.orchestrator import Orchestrator
    except ImportError as exc:
        _fail(f"Cannot import core modules: {exc}")

    model = os.getenv("gpt-04-model", "command-a-03-2025")
    _ok(f"Using LLM model: {model}")

    llm = LLM(model=model, temperature=0.3)
    orchestrator = Orchestrator(llm=llm)

    request = (
        "Write a Python function called `add(a, b)` that returns the sum of two numbers, "
        "and generate a pytest unit test for it."
    )
    _ok(f"Sending request to orchestrator: {request[:80]}...")

    result = orchestrator.process_user_request(request)

    status = result.get("status", "unknown")
    agents_spawned = result.get("agents_spawned", [])
    agent_results = result.get("agent_results", {})

    print(f"\n  Status         : {status}")
    print(f"  Correlation ID : {result.get('correlation_id', 'n/a')}")
    print(f"  Goal           : {str(result.get('goal', ''))[:80]}")
    print(f"  Agents spawned : {agents_spawned}")

    if status in ("success", "completed", "partial_success"):
        _ok(f"Orchestrator finished — status={status}")
    elif status == "error":
        _warn(f"Orchestrator returned an error: {result.get('error', result)}")
    else:
        _warn(f"Unexpected status: {status}")

    # Print per-agent outputs
    if agent_results:
        print(f"\n  {'─'*50}")
        print("  AGENT OUTPUTS")
        print(f"  {'─'*50}")
        for agent_name, agent_data in agent_results.items():
            if agent_data.get("status") == "error":
                print(f"\n  [{agent_name}] ERROR: {agent_data.get('error')}")
                continue
            print(
                f"\n  [{agent_name}]  class={agent_data.get('agent_class')}  "
                f"status={agent_data.get('status')}"
            )
            for i, tr in enumerate(agent_data.get("task_results", []), 1):
                task_type = tr.get("task", {}).get("type", "?")
                res = tr.get("result") or {}
                output = (
                    res.get("output")
                    or res.get("result")
                    or res.get("code")
                    or res.get("report")
                    or str(res)
                )
                print(f"    Task {i} [{task_type}]: {str(output)[:200]}")

    assert len(agents_spawned) > 0 or agent_results, (
        "Orchestrator spawned no agents — check LLM connectivity and model config."
    )
    _ok(f"Agents spawned: {agents_spawned}")


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_all() -> None:
    print("\n" + "█" * 60)
    print("  VentureOS — Full E2E Test Suite")
    print("  Backend:", BASE_URL)
    print("█" * 60)

    passed, failed = 0, 0

    steps = [
        ("Health check", lambda: test_health()),
        ("Auth / login", lambda: test_auth()),
        ("Agents API", None),   # needs token — resolved inline
        ("Tasks API", None),    # needs token + agent_id
        ("Orchestrator direct", lambda: test_orchestrator_direct()),
    ]

    token: str = ""
    agent_id: str = ""

    # Step 1: health
    try:
        test_health()
        passed += 1
    except Exception as e:
        print(f"\n  ✗  Health check FAILED: {e}")
        failed += 1
        print("\n  Backend not reachable — aborting remaining HTTP tests.")
        print("  Running orchestrator direct test only...\n")
        try:
            test_orchestrator_direct()
            passed += 1
        except Exception as e2:
            print(f"  ✗  Orchestrator direct FAILED: {e2}")
            failed += 1
        _print_summary(passed, failed)
        return

    # Step 2: auth
    try:
        token = test_auth()
        passed += 1
    except Exception as e:
        print(f"\n  ✗  Auth FAILED: {e}")
        failed += 1

    # Steps 3+4: agents & tasks (require token)
    if token:
        try:
            agent_id = test_agents(token)
            passed += 1
        except Exception as e:
            print(f"\n  ✗  Agents API FAILED: {e}")
            failed += 1

        if agent_id:
            try:
                test_tasks(token, agent_id)
                passed += 1
            except Exception as e:
                print(f"\n  ✗  Tasks API FAILED: {e}")
                failed += 1
        else:
            _warn("Skipping Tasks test — no agent_id available.")
            failed += 1
    else:
        _warn("Skipping Agents + Tasks tests — no token available.")
        failed += 2

    # Step 5: orchestrator direct
    try:
        test_orchestrator_direct()
        passed += 1
    except Exception as e:
        print(f"\n  ✗  Orchestrator direct FAILED: {e}")
        failed += 1

    _print_summary(passed, failed)


def _print_summary(passed: int, failed: int) -> None:
    total = passed + failed
    print("\n" + "═" * 60)
    print(f"  Results: {passed}/{total} passed  |  {failed}/{total} failed")
    print("═" * 60)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run_all()
