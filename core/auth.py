from fastapi import Header, HTTPException, status

def require_user(authorization: str | None = Header(default=None)) -> dict:
    """Validate a Supabase Auth bearer token. Reads stay public; every
    write route depends on this."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        from core.supabase_client import get_supabase_client
        result = get_supabase_client().auth.get_user(token)
        user = getattr(result, "user", None)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return {"id": str(getattr(user, "id", "")), "email": getattr(user, "email", "") or ""}

def actor_of(user: dict) -> str:
    return user.get("email") or user.get("id") or "unknown"
