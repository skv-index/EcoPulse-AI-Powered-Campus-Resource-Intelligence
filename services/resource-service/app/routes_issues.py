"""Issue endpoints: GET/POST /api/issues, PATCH /api/issues/<id>/status."""
from datetime import datetime, timezone
from flask import Blueprint, request
from app import ok, fail, serialize, parse_object_id
from app.db import issues_col
from app.models import validate_issue, validate_status_transition

bp = Blueprint("issues", __name__)


@bp.route("/api/issues", methods=["GET"])
def list_issues():
    flt = {}
    if request.args.get("status"):
        flt["status"] = request.args.get("status")
    if request.args.get("building_id"):
        flt["building_id"] = request.args.get("building_id")
    rows = list(issues_col().find(flt))
    rows.sort(key=lambda d: d.get("created_at"), reverse=True)
    return ok(serialize(rows))


@bp.route("/api/issues", methods=["POST"])
def create_issue():
    data = request.get_json(silent=True) or {}
    # Apply friendly defaults BEFORE validation.
    data = {"priority": "medium", "status": "open", **data}
    valid, errors = validate_issue(data)
    if not valid:
        return fail("VALIDATION_ERROR",
                    "Invalid issue: " + "; ".join(
                        f"{k}: {v}" for k, v in errors.items()), 400)
    doc = {
        "title": data["title"].strip(),
        "description": data.get("description", "").strip(),
        "building_id": str(data["building_id"]).strip(),
        "category": data["category"],
        "priority": data["priority"],
        "status": data["status"],
        "reported_by": data.get("reported_by", "anonymous"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    inserted_id = issues_col().insert_one(doc).inserted_id
    return ok(serialize(issues_col().find_one({"_id": inserted_id})), 201)


@bp.route("/api/issues/<iid>", methods=["GET"])
def get_issue(iid):
    oid = parse_object_id(iid)
    if oid is None:
        return fail("INVALID_ID", "Invalid issue id.", 400)
    doc = issues_col().find_one({"_id": oid})
    if not doc:
        return fail("NOT_FOUND", "Issue not found.", 404)
    return ok(serialize(doc))


@bp.route("/api/issues/<iid>/status", methods=["PATCH"])
def patch_issue_status(iid):
    oid = parse_object_id(iid)
    if oid is None:
        return fail("INVALID_ID", "Invalid issue id.", 400)
    doc = issues_col().find_one({"_id": oid})
    if not doc:
        return fail("NOT_FOUND", "Issue not found.", 404)
    body = request.get_json(silent=True) or {}
    valid, errors = validate_status_transition(body.get("status"))
    if not valid:
        return fail("VALIDATION_ERROR",
                    "Invalid status: " + "; ".join(
                        f"{k}: {v}" for k, v in errors.items()), 400)
    issues_col().update_one({"_id": oid}, {"$set": {
        "status": body["status"],
        "updated_at": datetime.now(timezone.utc),
    }})
    return ok(serialize(issues_col().find_one({"_id": oid})))
