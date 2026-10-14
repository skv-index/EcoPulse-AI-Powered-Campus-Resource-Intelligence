"""Reading endpoints: GET/POST /api/readings (+filters), GET/PUT/DELETE /<id>."""
from datetime import datetime, timezone
from flask import Blueprint, request
from app import ok, fail, serialize, parse_object_id
from app.db import readings_col, buildings_col
from app.models import validate_reading

bp = Blueprint("readings", __name__)


def _parse_dt(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


@bp.route("/api/readings", methods=["GET"])
def list_readings():
    flt = {}
    building_id = request.args.get("building_id")
    if building_id:
        # Accept either a raw string id or an ObjectId; store both forms safely.
        oid = parse_object_id(building_id)
        flt["building_id"] = str(oid) if oid else building_id
    if request.args.get("resource_type"):
        flt["resource_type"] = request.args.get("resource_type")
    # Time window: ?from=ISO&to=ISO filters on recorded_at.
    dt_from = _parse_dt(request.args.get("from")) if request.args.get("from") else None
    dt_to = _parse_dt(request.args.get("to")) if request.args.get("to") else None
    if request.args.get("from") and dt_from is None:
        return fail("INVALID_DATE", "Query param 'from' must be ISO8601.", 400)
    if request.args.get("to") and dt_to is None:
        return fail("INVALID_DATE", "Query param 'to' must be ISO8601.", 400)
    if dt_from or dt_to:
        flt["recorded_at"] = {}
        if dt_from:
            flt["recorded_at"]["$gte"] = dt_from
        if dt_to:
            flt["recorded_at"]["$lte"] = dt_to
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        return fail("INVALID_LIMIT", "Query param 'limit' must be an integer.", 400)
    limit = max(1, min(limit, 1000))

    rows = list(readings_col().find(flt))
    # Newest first, then apply limit in Python (works for both backends).
    rows.sort(key=lambda d: d.get("recorded_at"), reverse=True)
    return ok(serialize(rows[:limit]))


@bp.route("/api/readings", methods=["POST"])
def create_reading():
    data = request.get_json(silent=True) or {}
    valid, errors = validate_reading(data)
    if not valid:
        return fail("VALIDATION_ERROR",
                    "Invalid reading: " + "; ".join(
                        f"{k}: {v}" for k, v in errors.items()), 400)
    recorded_at = _parse_dt(data["recorded_at"]) if data.get("recorded_at") else datetime.now(timezone.utc)
    # Auto-fill building_name from the buildings collection when omitted.
    building_name = str(data.get("building_name", "") or "").strip()
    if not building_name:
        oid = parse_object_id(data["building_id"])
        if oid is not None:
            b = buildings_col().find_one({"_id": oid})
            if b:
                building_name = b.get("name", "")
    doc = {
        "building_id": str(data["building_id"]).strip(),
        "building_name": building_name,
        "resource_type": data["resource_type"],
        "value": data["value"],
        "unit": data["unit"],
        "recorded_at": recorded_at,
        "source": data.get("source", "manual"),
        "notes": data.get("notes", ""),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    inserted_id = readings_col().insert_one(doc).inserted_id
    return ok(serialize(readings_col().find_one({"_id": inserted_id})), 201)


@bp.route("/api/readings/<rid>", methods=["GET"])
def get_reading(rid):
    oid = parse_object_id(rid)
    if oid is None:
        return fail("INVALID_ID", "Invalid reading id.", 400)
    doc = readings_col().find_one({"_id": oid})
    if not doc:
        return fail("NOT_FOUND", "Reading not found.", 404)
    return ok(serialize(doc))


@bp.route("/api/readings/<rid>", methods=["PUT"])
def update_reading(rid):
    oid = parse_object_id(rid)
    if oid is None:
        return fail("INVALID_ID", "Invalid reading id.", 400)
    existing = readings_col().find_one({"_id": oid})
    if not existing:
        return fail("NOT_FOUND", "Reading not found.", 404)
    patch = request.get_json(silent=True) or {}
    # Merge then re-validate (recorded_at may arrive as ISO string or datetime).
    merged_raw = {**existing, **patch, "_id": existing["_id"]}
    check = dict(merged_raw)
    if isinstance(check.get("recorded_at"), datetime):
        check["recorded_at"] = check["recorded_at"].isoformat()
    valid, errors = validate_reading(check)
    if not valid:
        return fail("VALIDATION_ERROR",
                    "Invalid reading: " + "; ".join(
                        f"{k}: {v}" for k, v in errors.items()), 400)
    merged_raw["recorded_at"] = _parse_dt(check["recorded_at"])
    merged_raw["updated_at"] = datetime.now(timezone.utc)
    readings_col().update_one({"_id": oid}, {"$set": merged_raw})
    return ok(serialize(readings_col().find_one({"_id": oid})))


@bp.route("/api/readings/<rid>", methods=["DELETE"])
def delete_reading(rid):
    oid = parse_object_id(rid)
    if oid is None:
        return fail("INVALID_ID", "Invalid reading id.", 400)
    doc = readings_col().find_one({"_id": oid})
    if not doc:
        return fail("NOT_FOUND", "Reading not found.", 404)
    readings_col().delete_one({"_id": oid})
    return ok({"message": "Reading deleted.", "id": str(oid)})
