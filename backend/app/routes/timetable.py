import uuid
import threading
from flask import Blueprint, request, jsonify
from ..utils.auth_middleware import require_auth, require_role
from ..utils.supabase_client import sb
from ..agents.crew import generation_status

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/api/timetable/generate', methods=['POST'])
@require_auth
@require_role('admin')
def generate():
    generation_id = str(uuid.uuid4())
    generation_status[generation_id] = 'running'

    def run_crew():
        try:
            from ..agents.crew import run_scheduling_crew
            run_scheduling_crew(generation_id)
            # crew.py updates its own dict — sync it here too
            generation_status[generation_id] = 'completed'
        except Exception as e:
            generation_status[generation_id] = f'failed: {str(e)}'

    thread = threading.Thread(target=run_crew)
    thread.daemon = True
    thread.start()

    return jsonify({
        'generation_id': generation_id,
        'status': 'started'
    })


@timetable_bp.route('/api/timetable/status/<generation_id>', methods=['GET'])
@require_auth
def get_status(generation_id):
    status = generation_status.get(generation_id, 'not_found')
    return jsonify({
        'generation_id': generation_id,
        'status': status
    })

@timetable_bp.route('/api/timetable', methods=['GET'])
@require_auth
def get_timetable():
    try:
        semester   = request.args.get('semester')
        batch      = request.args.get('batch')
        faculty_id = request.args.get('faculty_id')
        status     = request.args.get('status', 'published')

        query = sb.table('timetable_entries') \
            .select('*, subjects(*), faculty(*), rooms(*), time_slots(*), batches(*)') \
            .eq('status', status)

        if semester:
            batch_ids = sb.table('batches') \
                .select('id') \
                .eq('semester', int(semester)) \
                .execute().data
            ids = [b['id'] for b in batch_ids]
            if ids:
                query = query.in_('batch_id', ids)
        if batch:
            query = query.eq('batches.batch_name', batch)
        if faculty_id:
            query = query.eq('faculty_id', faculty_id)

        result = query.execute()
        return jsonify(result.data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/api/timetable/publish/<generation_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def publish(generation_id):
    try:
        sb.table('timetable_entries') \
            .update({'status': 'published'}) \
            .eq('generation_id', generation_id) \
            .execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@timetable_bp.route('/api/timetable/entry/<entry_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def update_entry(entry_id):
    try:
        data           = request.json
        allowed_fields = ['faculty_id', 'room_id', 'time_slot_id']
        update_data    = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        result = sb.table('timetable_entries') \
            .update(update_data) \
            .eq('id', entry_id) \
            .execute()

        return jsonify({'success': True, 'data': result.data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500