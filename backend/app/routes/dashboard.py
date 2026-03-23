from flask import Blueprint, request, jsonify
from ..utils.auth_middleware import require_auth, require_role
from ..utils.supabase_client import sb

dashboard_bp = Blueprint('dashboard', __name__)
@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@require_auth
@require_role('admin')
def get_stats():
    try:
        faculty_count  = sb.table('faculty') \
                            .select('*', count='exact').execute()
        subject_count  = sb.table('subjects') \
                            .select('*', count='exact').execute()
        room_count     = sb.table('rooms') \
                            .select('*', count='exact').execute()
        published      = sb.table('timetable_entries') \
                            .select('*', count='exact') \
                            .eq('status', 'published').execute()

        return jsonify({
            'total_faculty':    faculty_count.count,
            'total_subjects':   subject_count.count,
            'total_rooms':      room_count.count,
            'timetable_status': 'published' if published.count > 0 else 'not_generated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/faculty-workload', methods=['GET'])
@require_auth
@require_role('admin')
def faculty_workload():
    try:
        result = sb.table('faculty_workload_summary') \
                    .select('*') \
                    .execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/subjects', methods=['GET'])
@require_auth
@require_role('admin')
def get_subjects():
    try:
        semester = request.args.get('semester')
        program  = request.args.get('program', 'BTech')

        query = sb.table('subjects').select('*').eq('program', program)
        if semester:
            query = query.eq('semester', int(semester))

        result = query.execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/faculty', methods=['GET'])
@require_auth
@require_role('admin')
def get_faculty():
    try:
        result = sb.table('faculty') \
                    .select('*') \
                    .eq('is_active', True) \
                    .execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/rooms', methods=['GET'])
@require_auth
@require_role('admin')
def get_rooms():
    try:
        result = sb.table('rooms').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500