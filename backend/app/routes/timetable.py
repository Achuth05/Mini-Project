import uuid
import threading
from flask import Blueprint, request, jsonify
from ..utils.auth_middleware import require_auth, require_role
from ..utils.supabase_client import sb
from ..agents.crew import generation_status, run_scheduling_crew

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/api/timetable/generate', methods=['POST'])
@require_auth
@require_role('admin')
def generate():
    # Use the semester from request body, default to 6 if not provided
    data = request.json or {}
    semester = data.get('semester', 6)
    
    generation_id = str(uuid.uuid4())
    generation_status[generation_id] = 'running'

    def run_crew():
        try:
            # The run_scheduling_crew function now handles the internal 
            # status updates and DB saving logic
            run_scheduling_crew(generation_id, semester=semester)
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
    
    # Check if status is the completed dictionary from run_scheduling_crew
    if isinstance(status, dict):
        return jsonify({
            'generation_id': generation_id,
            'status': status.get('status', 'unknown'),
            'result': status.get('result', None)
        })
        
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
        # Default to 'draft' or 'published' based on your workflow
        status     = request.args.get('status', 'draft') 

        query = sb.table('timetable_entries') \
            .select('*, subjects(*), faculty(*), rooms(*), time_slots(*), batches(*)')

        # Apply Filters
        if status:
            query = query.eq('status', status)
            
        if semester:
            # Filter batches by semester first to get IDs
            batch_res = sb.table('batches').select('id').eq('semester', int(semester)).execute()
            ids = [b['id'] for b in batch_res.data]
            if ids:
                query = query.in_('batch_id', ids)
                
        if batch:
            # Joins allow us to filter by the related table's columns
            query = query.eq('batches.batch_name', batch)
            
        if faculty_id:
            query = query.eq('faculty_id', faculty_id)

        # Order by day and slot for a logical view
        result = query.execute()
        return jsonify(result.data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@timetable_bp.route('/api/timetable/publish/<generation_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def publish(generation_id):
    try:
        # Move all entries from this specific run to 'published' status
        sb.table('timetable_entries') \
            .update({'status': 'published'}) \
            .eq('generation_id', generation_id) \
            .execute()
        return jsonify({'success': True, 'message': f'Generation {generation_id} published.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@timetable_bp.route('/api/timetable/entry/<entry_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def update_entry(entry_id):
    try:
        data = request.json
        # Allow admins to manually tweak the AI's results
        allowed_fields = ['faculty_id', 'room_id', 'time_slot_id', 'status']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        result = sb.table('timetable_entries') \
            .update(update_data) \
            .eq('id', entry_id) \
            .execute()

        return jsonify({'success': True, 'data': result.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500