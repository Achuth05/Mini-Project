import os
from functools import wraps
from flask import request, jsonify, g
from supabase import create_client, Client

# Initialize Supabase Client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY") # Use Service Role for admin-level role checks
supabase: Client = create_client(url, key)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Missing or invalid token"}), 401
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify JWT with Supabase Auth
            user = supabase.auth.get_user(token)
            # Attach user object to Flask's global 'g' for use in routes
            g.user = user.user
        except Exception as e:
            return jsonify({"message": "Authentication failed", "error": str(e)}), 401
            
        return f(*args, **kwargs)
    return decorated

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Ensure require_auth was called first
            if not hasattr(g, 'user'):
                return jsonify({"message": "Auth required before role check"}), 401
            
            # Query your 'profiles' table for the user's role
            user_id = g.user.id
            response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
            
            if not response.data or response.data.get("role") != required_role:
                return jsonify({"message": f"Access denied. Requires {required_role} role"}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator