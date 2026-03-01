from supabase import create_client, Client
import config

if not config.SUPABASE_URL or not config.SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing in environment variables.")

# Create single Supabase client instance
supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_KEY
)

# Export the client
__all__ = ["supabase"]