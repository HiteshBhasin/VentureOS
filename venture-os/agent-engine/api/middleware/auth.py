# Authentication middleware — Supabase JWT verification
import os

import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

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
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
            request.state.user_id = payload["sub"]
            request.state.user_email = payload.get("email", "")
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"detail": "Token has expired."})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token."})

        return await call_next(request)


def get_current_user(request: Request) -> str:
    """FastAPI dependency — returns the authenticated user_id or raises 401."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return user_id
