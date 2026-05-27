import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """
    Initializes and returns the Supabase client.
    Handles potential URL malformation (PGRST125) by stripping redundant paths.
    """
    raw_url = os.getenv("SUPABASE_URL", "").strip().strip('"').strip("'")
    url: str = raw_url.split("/rest/v1")[0].rstrip("/")
    key: str = os.getenv("SUPABASE_KEY", "").strip().strip('"').strip("'")
    
    if not url or not key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set in environment")
        
    return create_client(url, key)

supabase: Client = get_supabase_client()