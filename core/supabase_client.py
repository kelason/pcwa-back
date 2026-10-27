from supabase import create_client, Client
from core.config import supabase_url, supabase_key

_client: Client | None = None

def get_supabase_client() -> Client:
    """Lazy singleton so importing the app never requires credentials
    (tests run credential-free with overridden services)."""
    global _client
    if _client is None:
        url, key = supabase_url(), supabase_key()
        if not url or not key:
            raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set in environment")
        _client = create_client(url, key)
    return _client
