# Auth routes — signup, login, logout, me (powered by Supabase Auth)
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.middleware.auth import get_current_user
from memory.supabase_client import engine

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201)
async def signup(body: SignupRequest):
    """Register a new user via Supabase Auth and create their profile row."""
    try:
        res = engine.auth.sign_up({"email": body.email, "password": body.password})
        if res.user is None:
            raise HTTPException(
                status_code=400,
                detail="Signup failed. The email may already be registered.",
            )
        # Mirror the user into public.profiles for app-level data
        engine.table("profiles").insert({
            "id": res.user.id,
            "email": body.email,
            "name": body.name or "",
        }).execute()
        return {
            "user_id": res.user.id,
            "email": res.user.email,
            "message": "Signup successful. Check your email to confirm your account.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(body: LoginRequest):
    """Sign in with email + password. Returns a Supabase JWT access token."""
    try:
        res = engine.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        if res.session is None or res.user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "expires_in": res.session.expires_in,  # seconds until access_token expires
            "token_type": "bearer",
            "user_id": res.user.id,
            "email": res.user.email,
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    """Exchange a refresh token for a new access token."""
    try:
        res = engine.auth.refresh_session(body.refresh_token)
        if res.session is None or res.user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "expires_in": res.session.expires_in,
            "token_type": "bearer",
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")


@router.post("/logout")
async def logout():
    """Logout endpoint. Client should discard both tokens."""
    return {"message": "Logged out successfully."}


@router.get("/me")
async def me(user_id: str = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    res = (
        engine.table("profiles")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return res.data
