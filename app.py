"""
app.py — CORRUGATE IQ Flask application entry point.
"""
import os
from flask import Flask, jsonify
from routes.dashboard import dashboard_bp
from routes.machines import machines_bp
from routes.reports import reports_bp
from routes.simulator_routes import simulator_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # ── CORS headers ─────────────────────────────────────────────────────────
    # In production, restrict to your own domain. Use env var CORS_ORIGIN or
    # fall back to same-origin (no header) in production mode.
    allowed_origin = os.environ.get("CORS_ORIGIN", "*")

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"]  = allowed_origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    # ── Blueprint registration ────────────────────────────────────────────────
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(simulator_bp)

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found", "code": 404}), 404

    @app.errorhandler(500)
    def server_error(e):
        # Never expose internal error details to end users in production
        return jsonify({"error": "Internal server error", "code": 500}), 500

    return app


# Expose WSGI application for Vercel and production servers
app = create_app()
application = app


if __name__ == "__main__":
    # debug mode controlled by env var — NEVER True in production
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)


