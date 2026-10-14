"""Flask application factory for the AI microservice."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import jsonify, request
from flask_cors import CORS

from app.config import RESOURCE_SERVICE_URL


def _envelope_ok(data):
    return {"success": True, "data": data}


def _envelope_fail(message: str):
    return {"success": False, "error": message}


def create_app():
    """Build and configure the Flask app."""
    from flask import Flask

    app = Flask(__name__)
    CORS(app)  # allow the frontend dashboard to call us directly

    # --- blueprints -------------------------------------------------- #
    from app.routes_ai import ai_bp

    app.register_blueprint(ai_bp, url_prefix="/api/ai")

    # --- health ------------------------------------------------------ #
    @app.route("/api/health", methods=["GET"])
    def health():
        from app import resource_client

        rs = resource_client.ping()
        return (
            jsonify(
                _envelope_ok(
                    {
                        "status": "ok",
                        "service": "ai-service",
                        "resource_service": {
                            "url": RESOURCE_SERVICE_URL,
                            **rs,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            ),
            200,
        )

    # --- error handlers (always use the envelope) -------------------- #
    @app.errorhandler(404)
    def not_found(_err):
        return jsonify(_envelope_fail(f"Not found: {request.path}")), 404

    @app.errorhandler(405)
    def method_not_allowed(_err):
        return jsonify(_envelope_fail("Method not allowed.")), 405

    @app.errorhandler(500)
    def internal_error(_err):
        return jsonify(_envelope_fail("Internal server error.")), 500

    return app
