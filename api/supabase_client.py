"""Backward-compatible shim. New code uses core.supabase_client."""
from core.supabase_client import get_supabase_client

__all__ = ["get_supabase_client", "supabase"]


def __getattr__(name):
    if name == "supabase":
        return get_supabase_client()
    raise AttributeError(name)
