import os
from dotenv import load_dotenv

load_dotenv()

def supabase_url() -> str:
    raw = os.getenv("SUPABASE_URL", "").strip().strip('"').strip("'")
    return raw.split("/rest/v1")[0].rstrip("/")

def supabase_key() -> str:
    return os.getenv("SUPABASE_KEY", "").strip().strip('"').strip("'")

def frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173")
