# Agent Engine Implementation Guide

## File Reference

### Core Module (`core/`)

| File                | Purpose                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------ |
| `agent_factory.py`  | Creates, tracks, and manages agent instances. Registers agent types and spawns appropriate agents for tasks. |
| `orchestrator.py`   | Coordinates multiple agents working together. Manages task distribution and workflow execution.              |
| `meta_agent.py`     | High-level agent that can spawn and manage other agents. Makes decisions about which agents to use.          |
| `task_graph.py`     | Manages task dependencies as a directed graph. Determines execution order and parallelization.               |
| `budget_manager.py` | Tracks token usage, costs, and enforces budget limits across agents.                                         |
| `validator.py`      | Validates task inputs, agent outputs, and ensures data integrity.                                            |
| `llm_class.py`      | Wrapper for LLM API calls (OpenAI). Handles invocation with system/user prompts.                             |
| `exceptions.py`     | Custom exception hierarchy for error handling (AgentError, TaskError, BudgetExceededError, etc.).            |
| `events.py`         | Event bus system for agent communication. Publish/subscribe pattern for lifecycle events.                    |
| `state_machine.py`  | Manages agent state transitions (idle → running → completed). Validates legal transitions.                   |

### Agents Module (`agents/`)

| File                | Purpose                                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| `base_agent.py`     | Abstract base class all agents inherit from. Defines lifecycle, context, history, and execution interface. |
| `coding_agent.py`   | Specialized agent for code generation, editing, and programming tasks.                                     |
| `research_agent.py` | Agent for research, information gathering, and synthesis.                                                  |
| `review_agent.py`   | Agent for code review, content review, and quality assessment.                                             |
| `runtime_agent.py`  | Agent for executing code, running commands, and runtime operations.                                        |

### Memory Module (`memory/`)

| File                  | Purpose                                                                               |
| --------------------- | ------------------------------------------------------------------------------------- |
| `memory_manager.py`   | Central coordinator for all memory operations. Routes to appropriate storage backend. |
| `vector_store.py`     | Semantic memory using vector embeddings for similarity search.                        |
| `structured_store.py` | Key-value and structured data storage for agent state.                                |
| `cache_store.py`      | Short-term caching for frequently accessed data and LLM responses.                    |
| `audit_log.py`        | Immutable log of all agent actions for debugging and compliance.                      |

### Tools Module (`tools/`)

| File               | Purpose                                                                      |
| ------------------ | ---------------------------------------------------------------------------- |
| `tool_registry.py` | Registers and discovers available tools. Maps tool names to implementations. |
| `tool_executor.py` | Executes tools with input validation, error handling, and output formatting. |
| `code_executor.py` | Safely executes code snippets in sandboxed environments.                     |
| `file_handler.py`  | File operations: read, write, create, delete, search files.                  |
| `web_search.py`    | Web search integration for retrieving online information.                    |
| `scraper.py`       | Web scraping tool for extracting content from URLs.                          |
| `financial_api.py` | Financial data API integration (stocks, markets, etc.).                      |

### Models Module (`models/`)

| File              | Purpose                                                                        |
| ----------------- | ------------------------------------------------------------------------------ |
| `llm_router.py`   | Routes LLM requests to appropriate models based on task requirements and cost. |
| `model_config.py` | Configuration for different LLM models (tokens, pricing, capabilities).        |
| `embeddings.py`   | Text embedding generation for vector storage and semantic search.              |

### Schemas Module (`schemas/`)

| File              | Purpose                                                               |
| ----------------- | --------------------------------------------------------------------- |
| `task_schema.py`  | Pydantic models for task definitions, inputs, outputs, and results.   |
| `agent_schema.py` | Pydantic models for agent configuration, metrics, and spawn requests. |

### Utils Module (`utils/`)

| File         | Purpose                                                                     |
| ------------ | --------------------------------------------------------------------------- |
| `logger.py`  | Centralized logging with context tracking. AgentLogger for structured logs. |
| `helpers.py` | Common utilities: ID generation, timestamps, deep merge, token estimation.  |
| `retry.py`   | Retry logic with exponential backoff for handling transient failures.       |

### Monitoring Module (`monitoring/`)

| File         | Purpose                                                                  |
| ------------ | ------------------------------------------------------------------------ |
| `metrics.py` | Performance tracking: token usage, costs, task durations, success rates. |
| `tracer.py`  | Distributed tracing with spans for debugging complex agent workflows.    |

### API Module (`api/`)

| File                      | Purpose                               |
| ------------------------- | ------------------------------------- |
| `main.py`                 | FastAPI application entry point.      |
| `routes/agent_routes.py`  | REST endpoints for agent operations.  |
| `routes/task_routes.py`   | REST endpoints for task management.   |
| `routes/memory_routes.py` | REST endpoints for memory operations. |
| `middleware/auth.py`      | Authentication middleware.            |

### Config Module (`config/`)

| File          | Purpose                                                     |
| ------------- | ----------------------------------------------------------- |
| `settings.py` | Application configuration, environment variables, defaults. |

---

## Implementation Order

### Phase 1: Foundation

| Order | File                 | Why First                                                    |
| ----- | -------------------- | ------------------------------------------------------------ |
| 1     | `config/settings.py` | All modules need configuration (API keys, model names, etc.) |
| 2     | `utils/logger.py`    | Debugging is impossible without logging                      |
| 3     | `utils/helpers.py`   | Basic utilities used everywhere                              |
| 4     | `core/exceptions.py` | Error handling needed by everything                          |

### Phase 2: LLM & Memory Core

| Order | File                         | Why                            |
| ----- | ---------------------------- | ------------------------------ |
| 5     | `core/llm_class.py`          | Agents can't work without LLM  |
| 6     | `utils/retry.py`             | LLM calls need retry logic     |
| 7     | `memory/memory_manager.py`   | Agents need memory to function |
| 8     | `memory/structured_store.py` | Simple key-value storage first |

### Phase 3: Single Agent Working

| Order | File                     | Why                                       |
| ----- | ------------------------ | ----------------------------------------- |
| 9     | `agents/base_agent.py`   | Implement the abstract methods            |
| 10    | `core/state_machine.py`  | Agent lifecycle management                |
| 11    | `agents/coding_agent.py` | Pick ONE specialized agent to build first |
| 12    | `tools/tool_registry.py` | Agents need tools                         |
| 13    | `tools/file_handler.py`  | Most basic tool                           |

### Phase 4: Multi-Agent System

| Order | File                    | Why                   |
| ----- | ----------------------- | --------------------- |
| 14    | `core/agent_factory.py` | Spawn multiple agents |
| 15    | `core/task_graph.py`    | Task dependencies     |
| 16    | `core/orchestrator.py`  | Coordinate agents     |
| 17    | `core/events.py`        | Agent communication   |

### Phase 5: Polish & API

| Order | File                     | Why               |
| ----- | ------------------------ | ----------------- |
| 18    | `monitoring/metrics.py`  | Track performance |
| 19    | `core/budget_manager.py` | Control costs     |
| 20    | `api/main.py`            | Expose via REST   |

---

## System Design Patterns

### Architecture Pattern: **Event-Driven Microkernel**

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│                         Orchestrator                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Task Graph  │  │ Event Bus   │  │Budget Mgr   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                       Agent Factory                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Coding   │ │ Research │ │ Review   │ │ Runtime  │           │
│  │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│                      Core Services                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ LLM Router  │  │ Memory Mgr  │  │ Tool Exec   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                      External Services                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ OpenAI API  │  │ Vector DB   │  │ Redis Cache │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern                     | Where Used                       | Purpose                                             |
| --------------------------- | -------------------------------- | --------------------------------------------------- |
| **Factory**                 | `AgentFactory`                   | Create agents without specifying exact class        |
| **Abstract Factory**        | `BaseAgent` + specialized agents | Family of related agent objects                     |
| **Strategy**                | `LLMRouter`, `ToolExecutor`      | Swap algorithms (models, tools) at runtime          |
| **Observer/Pub-Sub**        | `EventBus`                       | Decoupled agent communication                       |
| **State Machine**           | `StateMachine`                   | Manage agent lifecycle states                       |
| **Chain of Responsibility** | Task execution pipeline          | Pass tasks through validation → execution → logging |
| **Singleton**               | `MetricsCollector`, `Tracer`     | Global instances for monitoring                     |
| **Dependency Injection**    | Throughout                       | Loose coupling, testability                         |
| **Repository**              | Memory stores                    | Abstract data access                                |
| **Decorator**               | `@retry`, logging                | Add behavior without modifying code                 |

### Data Flow

```
User Request
     │
     ▼
┌─────────────┐
│   API       │ ──► Validate input (Pydantic schemas)
└─────────────┘
     │
     ▼
┌─────────────┐
│ Orchestrator│ ──► Build task graph, determine dependencies
└─────────────┘
     │
     ▼
┌─────────────┐
│Agent Factory│ ──► Spawn appropriate agent(s)
└─────────────┘
     │
     ▼
┌─────────────┐
│   Agent     │ ──► Execute task using LLM + Tools
└─────────────┘
     │
     ├──► Memory (store context)
     ├──► Events (notify other agents)
     ├──► Metrics (track usage)
     │
     ▼
┌─────────────┐
│  Response   │ ──► Return result to user
└─────────────┘
```

### Concurrency Model

```python
# Async-first design
async def execute_task(task):
    async with agent_pool.acquire() as agent:
        result = await agent.execute(task)
    return result

# Task parallelization
async def execute_parallel(tasks):
    return await asyncio.gather(*[
        execute_task(t) for t in tasks
        if not t.has_dependencies()
    ])
```

### Error Handling Strategy

```
┌─────────────────────────────────────────┐
│           Exception Hierarchy            │
├─────────────────────────────────────────┤
│ AgentEngineError (base)                 │
│   ├── AgentError                        │
│   │     ├── AgentNotFoundError          │
│   │     ├── AgentExecutionError         │
│   │     └── AgentTimeoutError           │
│   ├── TaskError                         │
│   │     ├── TaskValidationError         │
│   │     └── TaskDependencyError         │
│   ├── LLMError                          │
│   │     ├── LLMRateLimitError (retry)   │
│   │     └── LLMResponseError            │
│   └── BudgetExceededError (stop)        │
└─────────────────────────────────────────┘
```

### Scaling Considerations

| Component | Scaling Strategy                                                                |
| --------- | ------------------------------------------------------------------------------- |
| API       | Horizontal (multiple instances behind load balancer)                            |
| Agents    | Worker pool with async execution                                                |
| Memory    | Redis cluster for cache, PostgreSQL for structured, Pinecone/Qdrant for vectors |
| LLM Calls | Rate limiting, request queuing, model fallback                                  |
| Events    | Message queue (Redis Pub/Sub, RabbitMQ) if distributed                          |

---

## First Milestone Checklist

- [ ] `config/settings.py` - Load API keys from environment
- [ ] `utils/logger.py` - Basic logging working
- [ ] `core/llm_class.py` - Can call OpenAI API
- [ ] `agents/base_agent.py` - `execute_task` returns LLM response
- [ ] `agents/coding_agent.py` - Generates code from prompt
- [ ] **Test**: Single agent executes one coding task end-to-end

---

## Tech Stack Recommendations

| Layer      | Technology              | Why                          |
| ---------- | ----------------------- | ---------------------------- |
| API        | FastAPI                 | Async, type hints, auto docs |
| Validation | Pydantic                | Type safety, serialization   |
| LLM        | OpenAI SDK / LiteLLM    | Multi-provider support       |
| Vector DB  | Qdrant / Pinecone       | Semantic search              |
| Cache      | Redis                   | Fast, pub/sub support        |
| Database   | PostgreSQL              | Structured data, reliability |
| Queue      | Celery + Redis          | Background task processing   |
| Monitoring | OpenTelemetry           | Distributed tracing          |
| Testing    | pytest + pytest-asyncio | Async test support           |

---

## Configuration Reference (`config/settings.py`)

The settings module uses Pydantic BaseSettings for type-safe environment variable loading.

### Usage

```python
from config.settings import settings

# Access settings
api_key = settings.OPENAI_API_KEY
model = settings.DEFAULT_LLM_MODEL
pricing = settings.MODEL_PRICING["gpt-4"]["input"]
```

### API Keys

| Setting             | Type            | Default | Description       |
| ------------------- | --------------- | ------- | ----------------- |
| `OPENAI_API_KEY`    | `Optional[str]` | `None`  | OpenAI API key    |
| `ANTHROPIC_API_KEY` | `Optional[str]` | `None`  | Anthropic API key |
| `COHERE_API_KEY`    | `Optional[str]` | `None`  | Cohere API key    |
| `GOOGLE_API_KEY`    | `Optional[str]` | `None`  | Google AI API key |

### Server Configuration

| Setting           | Type        | Default                                              | Description          |
| ----------------- | ----------- | ---------------------------------------------------- | -------------------- |
| `APP_NAME`        | `str`       | `"VentureOS Agent Engine"`                           | Application name     |
| `APP_VERSION`     | `str`       | `"0.1.0"`                                            | Application version  |
| `DEBUG`           | `bool`      | `False`                                              | Enable debug mode    |
| `HOST`            | `str`       | `"0.0.0.0"`                                          | Server host          |
| `PORT`            | `int`       | `8000`                                               | Server port          |
| `ALLOWED_ORIGINS` | `List[str]` | `["http://localhost:3000", "http://localhost:8000"]` | CORS allowed origins |

### Database Configuration

| Setting             | Type            | Default                         | Description                  |
| ------------------- | --------------- | ------------------------------- | ---------------------------- |
| `DATABASE_URL`      | `Optional[str]` | `"sqlite:///./agent_engine.db"` | Database connection URL      |
| `REDIS_URL`         | `Optional[str]` | `"redis://localhost:6379/0"`    | Redis connection URL         |
| `VECTOR_DB_URL`     | `Optional[str]` | `None`                          | Vector DB URL (Qdrant, etc.) |
| `VECTOR_DB_API_KEY` | `Optional[str]` | `None`                          | Vector DB API key            |

### Logging Configuration

| Setting          | Type            | Default                                                  | Description        |
| ---------------- | --------------- | -------------------------------------------------------- | ------------------ |
| `LOG_LEVEL`      | `str`           | `"INFO"`                                                 | Logging level      |
| `LOG_FORMAT`     | `str`           | `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` | Log message format |
| `LOG_FILE`       | `Optional[str]` | `None`                                                   | Log file path      |
| `LOG_TO_CONSOLE` | `bool`          | `True`                                                   | Log to console     |

### LLM Defaults

| Setting                         | Type    | Default   | Description          |
| ------------------------------- | ------- | --------- | -------------------- |
| `DEFAULT_LLM_MODEL`             | `str`   | `"gpt-4"` | Default LLM model    |
| `DEFAULT_LLM_TEMPERATURE`       | `float` | `0.7`     | Sampling temperature |
| `DEFAULT_LLM_MAX_TOKENS`        | `int`   | `2048`    | Max response tokens  |
| `DEFAULT_LLM_TOP_P`             | `float` | `1.0`     | Top-p sampling       |
| `DEFAULT_LLM_FREQUENCY_PENALTY` | `float` | `0.0`     | Frequency penalty    |

### Memory Defaults

| Setting                               | Type   | Default | Description              |
| ------------------------------------- | ------ | ------- | ------------------------ |
| `DEFAULT_MEMORY_SHORT_TERM_ENABLED`   | `bool` | `True`  | Enable short-term memory |
| `DEFAULT_MEMORY_LONG_TERM_ENABLED`    | `bool` | `True`  | Enable long-term memory  |
| `DEFAULT_MEMORY_MAX_HISTORY`          | `int`  | `100`   | Max history entries      |
| `DEFAULT_MEMORY_VECTOR_STORE_ENABLED` | `bool` | `False` | Enable vector store      |

### Budget Defaults

| Setting                               | Type              | Default | Description                     |
| ------------------------------------- | ----------------- | ------- | ------------------------------- |
| `DEFAULT_BUDGET_MAX_TOKENS`           | `Optional[int]`   | `None`  | Max tokens per task (unlimited) |
| `DEFAULT_BUDGET_MAX_COST`             | `Optional[float]` | `10.0`  | Max cost in USD per task        |
| `DEFAULT_BUDGET_MAX_REQUESTS`         | `Optional[int]`   | `100`   | Max LLM requests per task       |
| `DEFAULT_BUDGET_MAX_DURATION_SECONDS` | `Optional[int]`   | `300`   | Max execution time (5 min)      |

### Model Pricing (per 1K tokens)

| Model             | Input Cost | Output Cost |
| ----------------- | ---------- | ----------- |
| `gpt-4`           | $0.030     | $0.060      |
| `gpt-4-turbo`     | $0.010     | $0.030      |
| `gpt-4o`          | $0.005     | $0.015      |
| `gpt-4o-mini`     | $0.00015   | $0.0006     |
| `gpt-3.5-turbo`   | $0.0005    | $0.0015     |
| `claude-3-opus`   | $0.015     | $0.075      |
| `claude-3-sonnet` | $0.003     | $0.015      |
| `claude-3-haiku`  | $0.00025   | $0.00125    |

### Available Models

```python
AVAILABLE_MODELS = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-3.5-turbo",
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
]
```

### Task Execution

| Setting                | Type    | Default | Description                  |
| ---------------------- | ------- | ------- | ---------------------------- |
| `TASK_DEFAULT_TIMEOUT` | `int`   | `300`   | Task timeout in seconds      |
| `TASK_MAX_RETRIES`     | `int`   | `3`     | Max retry attempts           |
| `TASK_RETRY_DELAY`     | `float` | `1.0`   | Initial retry delay (sec)    |
| `TASK_PARALLEL_LIMIT`  | `int`   | `5`     | Max parallel task executions |

### Rate Limiting

| Setting                          | Type  | Default  | Description             |
| -------------------------------- | ----- | -------- | ----------------------- |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `int` | `60`     | Max API requests/minute |
| `RATE_LIMIT_TOKENS_PER_MINUTE`   | `int` | `100000` | Max tokens/minute       |

### Cache Configuration

| Setting             | Type   | Default | Description             |
| ------------------- | ------ | ------- | ----------------------- |
| `CACHE_ENABLED`     | `bool` | `True`  | Enable response caching |
| `CACHE_TTL_SECONDS` | `int`  | `3600`  | Cache TTL (1 hour)      |
| `CACHE_MAX_SIZE`    | `int`  | `1000`  | Max cache entries       |

### Embedding Configuration

| Setting                | Type  | Default                    | Description                 |
| ---------------------- | ----- | -------------------------- | --------------------------- |
| `EMBEDDING_MODEL`      | `str` | `"text-embedding-3-small"` | Embedding model             |
| `EMBEDDING_DIMENSIONS` | `int` | `1536`                     | Embedding vector dimensions |

### Agent Types

```python
AGENT_TYPES = [
    "base",
    "react",
    "reflex",
    "task-specific",
    "custom",
]
```

### Tool Configuration

Default tools available (all enabled by default):

| Tool Category       | Tools Included                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| **Development**     | code_execution, code_generation, code_review, debugging, testing, deployment, version_control     |
| **Communication**   | email, calendar, communication, collaborative_editing                                             |
| **Data & Analysis** | data_analysis, data_visualization, financial_analysis, sentiment_analysis                         |
| **Research**        | web_search, market_research, knowledge_base                                                       |
| **Content**         | summarization, translation, question_answering, report_generation                                 |
| **Management**      | project_management, time_management, resource_management, budget_monitoring, performance_tracking |
| **Business**        | customer_support, hr_management, sales, marketing                                                 |
| **Other**           | file_management, api_access, social_media, custom_tool                                            |

---

## Environment Variables (.env)

Create a `.env` file in the `agent-engine/` directory:

```bash
# API Keys (Required)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Server
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./agent_engine.db
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_TO_CONSOLE=true

# LLM
DEFAULT_LLM_MODEL=gpt-4o
DEFAULT_LLM_TEMPERATURE=0.7

# Budget
DEFAULT_BUDGET_MAX_COST=10.0
DEFAULT_BUDGET_MAX_REQUESTS=100

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Cache
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

See `.env.example` for a complete template.
