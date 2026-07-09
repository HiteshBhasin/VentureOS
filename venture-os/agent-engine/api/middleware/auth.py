# Authentication middleware — Supabase JWT verification
import os

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# api/middleware/auth.py -> middleware -> api -> agent-engine (where .env lives)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
_SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
_supabase: Client | None = None


def _get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(_SUPABASE_URL, _SUPABASE_KEY)
    return _supabase


# Routes that do NOT require a valid JWT
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/signup",
    "/api/v1/auth/refresh",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Verify Supabase JWT on every request except public paths."""

    async def dispatch(self, request: Request, call_next):
        # Always allow preflight and public routes
        if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header. Expected: Bearer <token>"},
            )

        token = auth_header[7:].strip()
        try:
            user_response = _get_supabase().auth.get_user(token)
            if user_response is None or user_response.user is None:
                return JSONResponse(status_code=401, content={"detail": "Invalid token."})
            request.state.user_id = user_response.user.id
            request.state.user_email = user_response.user.email or ""
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Invalid token."})

        return await call_next(request)


def get_current_user(request: Request) -> str:
    """FastAPI dependency — returns the authenticated user_id or raises 401."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user_id
