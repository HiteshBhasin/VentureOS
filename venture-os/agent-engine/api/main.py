"""FastAPI entry point for VentureOS Agent Engine."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Allow running as `python main.py` from inside api/ OR as a module from agent-engine/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.auth import AuthMiddleware
from api.routes.agent_routes import router as agent_router
from api.routes.auth_routes import router as auth_router
from api.routes.memory_routes import router as memory_router
from api.routes.task_routes import router as task_router

from core.llm_class import LLM  # noqa: F401
from core.orchestrator import Orchestrator  # noqa: F401

# Comma-separated list of allowed origins in .env, e.g.:
# ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

LLM_MODEL = os.getenv("gpt-04-model", "command-a-03-2025")
llm = LLM(model=LLM_MODEL)
orchestrator = Orchestrator(llm=llm)


app = FastAPI(
    title="VentureOS Agent Engine",
    version="2.0.4",
    description="Orchestration backend for VentureOS agents and tasks",
)

# Order matters: CORS must be added before AuthMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(task_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")

app.state.orchestrator = orchestrator  # type: ignore


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": "2.0.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
