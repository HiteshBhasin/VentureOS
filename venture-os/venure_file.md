venture-os/agent-engine/
├── core/                    # Meta-Agent & Task Graph
│   ├── __init__.py
│   ├── meta_agent.py
│   ├── task_graph.py
│   ├── orchestrator.py
│   ├── agent_factory.py
│   ├── budget_manager.py
│   └── validator.py
├── agents/                  # Base Agents
│   ├── __init__.py
│   ├── base_agent.py
│   ├── runtime_agent.py
│   ├── research_agent.py
│   ├── coding_agent.py
│   └── review_agent.py
├── tools/                   # Tool Execution
│   ├── __init__.py
│   ├── tool_registry.py
│   ├── tool_executor.py
│   ├── web_search.py
│   ├── scraper.py
│   ├── financial_api.py
│   ├── code_executor.py
│   └── file_handler.py
├── memory/                  # Memory Write
│   ├── __init__.py
│   ├── memory_manager.py
│   ├── vector_store.py
│   ├── structured_store.py
│   ├── cache_store.py
│   └── audit_log.py
├── models/                  # LLM & Embeddings
│   ├── __init__.py
│   ├── llm_router.py
│   ├── embeddings.py
│   └── model_config.py
├── api/                     # FastAPI Interface
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   ├── schemas/
│   └── middleware/
├── config/
├── tests/
├── requirements.txt
├── Dockerfile
└── pyproject.toml