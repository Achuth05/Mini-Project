
from flask import Flask, jsonify
from flask_cors import CORS
from .config import SECRET_KEY, FLASK_ENV


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['ENV'] = FLASK_ENV
    app.config['DEBUG'] = FLASK_ENV == 'development'

    # ── CORS ──────────────────────────────────────────────────────────
    CORS(app,
         origins=["http://localhost:5173"],
         allow_headers=["Authorization", "Content-Type"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         supports_credentials=True
    )

    # ── Register Blueprints ───────────────────────────────────────────
    from .routes.auth      import auth_bp
    from .routes.upload    import upload_bp
    from .routes.dashboard import dashboard_bp
    from .routes.timetable import timetable_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(timetable_bp)

    # ── Global Error Handlers ─────────────────────────────────────────
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized", "status": 401}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Forbidden", "status": 403}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found", "status": 404}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error", "status": 500}), 500

    # ── Health Check ──────────────────────────────────────────────────
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok", "env": FLASK_ENV})

    return app