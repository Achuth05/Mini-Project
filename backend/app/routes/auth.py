from flask import Blueprint, jsonify, g, request
from ..utils.auth_middleware import require_auth
from ..utils.supabase_client import sb

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'message': 'Request must be JSON'}), 400
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        # 1. Attempt Supabase Authentication
        try:
            auth_response = sb.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as auth_err:
            print(f"Auth error: {str(auth_err)}")
            return jsonify({'message': 'Invalid email or password', 'error': str(auth_err)}), 401

        if not auth_response.user or not auth_response.session:
            return jsonify({'message': 'Login failed: No session returned'}), 401

        # 2. Fetch Profile Data using 'full_name' column
        try:
            # We select 'full_name' because that is what exists in your DB
            result = sb.table('profiles') \
                .select('full_name, role') \
                .eq('id', auth_response.user.id) \
                .single() \
                .execute()
            
            profile_data = result.data
            
            if not profile_data:
                return jsonify({'message': 'Profile data is empty in database'}), 404

        except Exception as prof_err:
            print(f"Profile Database Error for UID {auth_response.user.id}: {str(prof_err)}")
            return jsonify({
                'message': 'User authenticated, but profile record not found.',
                'error': str(prof_err)
            }), 404

        # 3. Success Response
        return jsonify({
            'token': auth_response.session.access_token,
            'user': {
                'id': auth_response.user.id,
                'email': auth_response.user.email,
                'name': profile_data.get('full_name', 'User'),
                'role': profile_data.get('role', 'student')
            },
            'role': profile_data.get('role', 'student'),
            'name': profile_data.get('full_name', 'User')
        }), 200

    except Exception as e:
        print(f"Server Crash: {str(e)}")
        return jsonify({'message': 'Internal Server Error', 'error': str(e)}), 500

@auth_bp.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    try:
        # Assuming g.user.id is populated by your @require_auth middleware
        result = sb.table('profiles').select('*').eq('id', g.user.id).single().execute()
        return jsonify(result.data), 200
    except Exception as e:
        print(f"Get Me Error: {str(e)}")
        return jsonify({'error': str(e)}), 500