import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
FLASK_ENV = os.getenv("FLASK_ENV")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
FLASK_ENV = os.getenv("FLASK_ENV", "production")
PORT = 5000

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
# service key is used by both flask and supabase configuration
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Optional: Validate required variables
required_vars = {
    "SECRET_KEY": SECRET_KEY,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
}

for var_name, value in required_vars.items():
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")