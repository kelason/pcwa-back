"""Supabase Auth proxy: the frontend never talks to Supabase Auth directly,
it logs in here and then sends the returned token as a Bearer header."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.auth import require_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    try:
        from core.supabase_client import get_supabase_client
        result = get_supabase_client().auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid email or password")
    session = getattr(result, "session", None)
    user = getattr(result, "user", None)
    if session is None or user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid email or password")
    return {
        "access_token": session.access_token,
        "user": {"id": str(user.id), "email": user.email or ""},
    }


@router.get("/me")
async def me(user: dict = Depends(require_user)):
    return user
