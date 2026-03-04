from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing in environment variables.")

# Create single Supabase client instance
sb: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# Export the client
__all__ = ["sb"]