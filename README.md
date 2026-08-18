# VentureOS — Autonomous Enterprise Framework (AEF)

AEF is a durable, multi-agent task-execution engine built for the CockroachDB × AWS
"Agentic Memory" hackathon. Its core claim: an agent's memory — task state, decision
history, and situational context — should survive a crashed process, a killed node, or
a full restart without losing or duplicating a single step of work.

CockroachDB is AEF's persistent memory layer. Every piece of agent state — the work
queue, decision/context history, and situational embeddings — lives in CockroachDB, not
in application memory. Kill the worker process mid-task and nothing is lost; a live
task's lease simply expires and another worker (or the same one, restarted) picks it
back up exactly where it left off.

## Demo scenario: emergency wildfire coordination

The included demo runs a 4-step emergency-coordination plan — **assess route → clear
zone → dispatch → re-plan** — against a fake wildfire incident. Each step is its own
durable row in CockroachDB's `tasks` table, not an in-memory call stack, so the same
crash-survival guarantee that protects the queue also protects a multi-step agentic
plan mid-execution.

```
venture-os/agent-engine/scripts/seed_wildfire_incident.py   # seeds the incident, kicks off step 1
venture-os/agent-engine/worker.py                            # claims/runs/chains the 4 steps
```

## CockroachDB tools used

- **Distributed Vector Indexing** — `public.memory_items` (schema in
  `scripts/cocroach_migrate_db.py`) stores agent memory as `embedding VECTOR(1024)`
  with a `VECTOR INDEX`, queried by cosine distance (`embedding <=> $1`) for nearest-
  neighbor situational recall — e.g. "have we seen a route-blockage incident like this
  before?" — with no separate vector store to keep in sync with the operational data.
- **CockroachDB Cloud Managed MCP Server** — the agent's read path into the cluster.
  Wired as two tools on the orchestrator's tool registry
  (`cockroach_cluster_list_tools`, `cockroach_cluster_read` in
  `core/orchestrator.py`, backed by `tools/bedrock_mcp_tool.py`), so an agent reads
  cluster data through the managed MCP endpoint rather than a hand-rolled DB
  connection.

## AWS service used

- **Amazon S3** — every completed task's result is archived to S3 as a durable audit
  artifact (`worker.py`, `_archive_result_to_s3`), keyed `tasks/<goal_id>/<task_id>.json`.
  CockroachDB remains the source of truth for task state; S3 is an external copy for
  inspection, not a dependency — a task still completes normally if S3 isn't configured
  or the write fails.

## Architecture

```
orchastrator/dashboard/        Next.js dashboard (agents, tasks, memory, logs)
venture-os/agent-engine/
    api/                       FastAPI — task/agent/memory CRUD, auth, live SSE stream
    worker.py                  Polls CockroachDB, claims tasks (SKIP LOCKED), executes,
                                chains the emergency-plan steps, archives to S3
    core/orchestrator.py       Spawns agents, routes tasks, registers tools (incl. MCP)
    core/llm_class.py          LLM provider client (OpenAI / Gemini / Mistral / Cohere)
    memory/                    Memory manager, vector store, structured store
    scripts/
        cocroach_migrate_db.py     Schema migration — run against the CockroachDB cluster
        cocroach_tools.py          Embeddings (Mistral) + memory_items read/write helpers
        seed_wildfire_incident.py  Seeds the demo incident
```

## Setup

### 1. Python environment (agent-engine)

```bash
cd venture-os/agent-engine
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Configure `.env`

Copy `.env` and fill in (see the file for the full list):

| Variable | Purpose |
| --- | --- |
| `COCRAOCH_DB_URL` | CockroachDB Cloud connection string — the queue, memory_items, and vector index all live here |
| `DATABASE_URL` | Postgres connection used by the dashboard/API's DB client |
| `SUPABASE_URL` / `SUPABASE_KEY` / `SUPABASE_SERVICE_KEY` | Dashboard/API auth + REST layer |
| `MISTRAL_API_KEY` | LLM generation + embeddings (`mistral-embed`, 1024-dim) |
| `OPENAI_API_KEY`, `GOOGLE_GEMINI_API_KEY`, `COHERE_API_KEY` | Alternate LLM providers (optional) |
| `AWS_S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | S3 task-result archiving (optional — worker degrades gracefully if unset) |

### 3. Migrate the CockroachDB schema

```bash
python scripts/cocroach_migrate_db.py
```

Creates `profiles`, `agents`, `tasks` (with the hash-bucketed queue columns), and
`memory_items` (with the vector index) on the CockroachDB cluster.

### 4. Run it

```bash
# Terminal 1 — API server (http://localhost:8000)
python api/main.py

# Terminal 2 — background worker (claims and executes tasks)
python worker.py

# Terminal 3 — seed the wildfire demo incident
python scripts/seed_wildfire_incident.py
```

The seed script prints a `goal_id` and a SQL query — run that query against the
CockroachDB cluster to watch the 4 steps (`assess_route → clear_zone → dispatch →
re_plan`) complete in order as the worker processes them.

### 5. Dashboard (optional)

```bash
cd orchastrator/dashboard
npm install
npm run dev
```

## License

See [LICENSE](LICENSE).
