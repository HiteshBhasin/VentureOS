# Authentication middleware
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuthType(Enum):
    """Authentication types."""

    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class Permission(Enum):
    """API permissions."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class AuthUser:
    """Authenticated user information."""

    user_id: str
    username: str
    permissions: List[Permission]
    metadata: Dict[str, Any]


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware."""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process authentication for request."""
        pass


# ==================== API Key Authentication ====================


def validate_api_key(api_key: str) -> bool:
    """Validate API key."""
    pass


def get_user_by_api_key(api_key: str) -> Optional[AuthUser]:
    """Get user associated with API key."""
    pass


def generate_api_key(user_id: str, permissions: List[Permission]) -> str:
    """Generate new API key."""
    pass


def revoke_api_key(api_key: str) -> bool:
    """Revoke an API key."""
    pass


def list_api_keys(user_id: str) -> List[Dict[str, Any]]:
    """List API keys for user."""
    pass


# ==================== JWT Authentication ====================


def create_jwt_token(user: AuthUser, expires_in: int = 3600) -> str:
    """Create JWT token."""
    pass


def validate_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate JWT token and return claims."""
    pass


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode JWT token without validation."""
    pass


def refresh_jwt_token(token: str) -> Optional[str]:
    """Refresh JWT token."""
    pass


def revoke_jwt_token(token: str) -> bool:
    """Revoke JWT token."""
    pass


def get_jwt_secret() -> str:
    """Get JWT secret key."""
    pass


def set_jwt_secret(secret: str) -> None:
    """Set JWT secret key."""
    pass


# ==================== Authorization ====================


def check_permission(user: AuthUser, permission: Permission) -> bool:
    """Check if user has permission."""
    pass


def require_permission(permission: Permission):
    """Decorator to require permission."""
    pass


def require_permissions(permissions: List[Permission]):
    """Decorator to require multiple permissions."""
    pass


def check_resource_access(user: AuthUser, resource_id: str, action: str) -> bool:
    """Check access to specific resource."""
    pass


def get_allowed_resources(user: AuthUser, action: str) -> List[str]:
    """Get resources user can access."""
    pass


# ==================== Rate Limiting ====================


def check_rate_limit(api_key: str, endpoint: str) -> bool:
    """Check if request is within rate limit."""
    pass


def get_rate_limit_status(api_key: str) -> Dict[str, Any]:
    """Get rate limit status."""
    pass


def set_rate_limit(api_key: str, requests_per_minute: int) -> None:
    """Set rate limit for API key."""
    pass


def reset_rate_limit(api_key: str) -> None:
    """Reset rate limit counter."""
    pass


# ==================== Session Management ====================


def create_session(user: AuthUser) -> str:
    """Create user session. Returns session ID."""
    pass


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session data."""
    pass


def update_session(session_id: str, data: Dict[str, Any]) -> bool:
    """Update session data."""
    pass


def delete_session(session_id: str) -> bool:
    """Delete session."""
    pass


def cleanup_expired_sessions() -> int:
    """Clean up expired sessions. Returns count deleted."""
    pass


# ==================== Utilities ====================


def extract_token(request: Request) -> Optional[str]:
    """Extract authentication token from request."""
    pass


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    pass


def verify_api_key_hash(api_key: str, hashed: str) -> bool:
    """Verify API key against hash."""
    pass


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    pass


def log_auth_event(
    event_type: str, user_id: Optional[str], details: Dict[str, Any]
) -> None:
    """Log authentication event."""
    pass
