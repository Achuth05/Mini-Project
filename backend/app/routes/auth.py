from flask import Blueprint, jsonify, g
from ..utils.auth_middleware import require_auth
from ..utils.supabase_client import sb

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    try:
        profile = sb.table('profiles') \
            .select('*') \
            .eq('id', g.user.id) \
            .single() \
            .execute()
        return jsonify(profile.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500