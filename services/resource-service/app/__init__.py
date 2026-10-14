"""App factory — creates the Flask app, registers Blueprints, error handlers.

Viva: create_app() wires Flask + CORS, mounts one Blueprint per resource,
and guarantees EVERY response (even 404/500) uses the standard envelope:
{"success": bool, "data": any, "error": {"code","message"} | None}.
"""
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

try:
    from bson import ObjectId
except ImportError:  # pragma: no cover
    ObjectId = None


# ---------------------------------------------------------------------------
# Envelope helpers (imported by all route modules)
# ---------------------------------------------------------------------------

def ok(data, status=200):
    return jsonify({"success": True, "data": data, "error": None}), status


def fail(code, message, status=400):
    return jsonify({"success": False, "data": None,
                    "error": {"code": code, "message": message}}), status


def serialize(doc):
    """Convert Mongo types (ObjectId/datetime) to JSON-safe values."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize(d) for d in doc]
    if isinstance(doc, dict):
        out = {}
        for k, v in doc.items():
            if ObjectId is not None and isinstance(v, ObjectId):
                out[k] = str(v)
            elif isinstance(v, datetime):
                out[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                out[k] = serialize(v)
            else:
                out[k] = v
        # Expose `_id` as `id` too (frontend-friendly), keep `_id` as well.
        if "_id" in out and "id" not in out:
            out["id"] = out["_id"]
        return out
    return doc


def parse_object_id(value):
    """Return ObjectId or None when the string is not a valid id."""
    if ObjectId is None:
        return None
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def create_app():
    app = Flask(__name__)
    CORS(app)  # allow the frontend (different port) to call this API

    # -- Blueprints (one file per resource keeps code viva-explainable) -----
    from app.routes_buildings import bp as buildings_bp
    from app.routes_readings import bp as readings_bp
    from app.routes_issues import bp as issues_bp
    from app.routes_dashboard import bp as dashboard_bp
    app.register_blueprint(buildings_bp)
    app.register_blueprint(readings_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(dashboard_bp)

    # -- Health check --------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health():
        from app import db as _db
        try:
            _db.get_db()["buildings"].count_documents({})
            db_status = "memory" if isinstance(
                _db.get_db(), _db.InMemoryDB) else "mongodb"
        except Exception:
            db_status = "unknown"
        return jsonify({"success": True,
                        "data": {"status": "ok",
                                 "service": "resource-service",
                                 "db": db_status},
                        "error": None}), 200

    # -- Envelope error handlers (never leak HTML error pages) ---------------
    @app.errorhandler(400)
    def _bad_request(e):
        return fail("BAD_REQUEST", "Bad request.", 400)

    @app.errorhandler(404)
    def _not_found(e):
        return fail("NOT_FOUND", "Route not found.", 404)

    @app.errorhandler(405)
    def _method_not_allowed(e):
        return fail("METHOD_NOT_ALLOWED", "Method not allowed.", 405)

    @app.errorhandler(500)
    def _server_error(e):
        return fail("INTERNAL_ERROR", "Internal server error.", 500)

    return app
