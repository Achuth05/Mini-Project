import os
import tempfile
from flask import Blueprint, request, jsonify
from ..utils.auth_middleware import require_auth, require_role
from ..utils.supabase_client import sb
from ..utils.excel_parser import parse_excel, validate_allotments, insert_allotments

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/api/upload', methods=['POST'])
@require_auth
@require_role('admin')
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Only .xlsx files accepted'}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        allotments, warnings    = parse_excel(tmp_path)
        validation_errors       = validate_allotments(allotments)
        hard_errors             = [e for e in validation_errors if e.startswith('ERROR')]

        if hard_errors:
            return jsonify({'success': False, 'errors': hard_errors}), 400

        result = insert_allotments(sb, allotments)

        return jsonify({
            'success':  True,
            'inserted': result['inserted'],
            'skipped':  result['skipped'],
            'warnings': warnings,
            'errors':   result['errors']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)