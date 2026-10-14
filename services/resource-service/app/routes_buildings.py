"""Building endpoints: GET/POST /api/buildings, GET/PUT/DELETE /api/buildings/<id>."""
from datetime import datetime, timezone
from flask import Blueprint, request
from app import ok, fail, serialize, parse_object_id
from app.db import buildings_col
from app.models import validate_building

bp = Blueprint("buildings", __name__)


@bp.route("/api/buildings", methods=["GET"])
def list_buildings():
    docs = buildings_col().find()
    # pymongo returns a cursor; the memory fallback returns a list.
    docs = list(docs)
    return ok(serialize(docs))


@bp.route("/api/buildings", methods=["POST"])
def create_building():
    data = request.get_json(silent=True) or {}
    valid, errors = validate_building(data)
    if not valid:
        return fail("VALIDATION_ERROR",
                    "Invalid building: " + "; ".join(
                        f"{k}: {v}" for k, v in errors.items()), 400)
    # `code` must stay unique — viva: app-level check (plus a DB index in prod).
    if buildings_col().find_one({"code": data["code"].strip()}):
        return fail("DUPLICATE_CODE",
                    f"Building code '{data['code'].strip()}' already exists.", 400)
    doc = {
        "name": data["name"].strip(),
        "code": data["code"].strip(),
        "type": data["type"],
        "floors": data.get("floors", 1),
        "area_sqft": data.get("area_sqft", 0),
        "department": data.get("department", ""),
        "location": data.get("location", ""),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    inserted_id = buildings_col().insert_one(doc).inserted_id
    saved = buildings_col().find_one({"_id": inserted_id})
    return ok(serialize(saved), 201)


@bp.route("/api/buildings/<bid>", methods=["GET"])
def get_building(bid):
    oid = parse_object_id(bid)
    if oid is None:
        return fail("INVALID_ID", "Invalid building id.", 400)
    doc = buildings_col().find_one({"_id": oid})
    if not doc:
        return fail("NOT_FOUND", "Building not found.", 404)
    return ok(serialize(doc))


@bp.route("/api/buildings/<bid>", methods=["PUT"])
def update_building(bid):
    oid = parse_object_id(bid)
    if oid is None:
        return fail("INVALID_ID", "Invalid building id.", 400)
    existing = buildings_col().find_one({"_id": oid})
    if not existing:
        return fail("NOT_FOUND", "Building not found.", 404)
    patch = request.get_json(silent=True) or {}
    merged = {**existing, **patch, "_id": existing["_id"]}
    valid, errors = validate_building(merged)
    if not valid:
        return fail("VALIDATION_ERROR",
                    "Invalid building: " + "; ".join(
                        f"{k}: {v}" for k, v in errors.items()), 400)
    if merged["code"] != existing["code"] and \
            buildings_col().find_one({"code": merged["code"]}):
        return fail("DUPLICATE_CODE",
                    f"Building code '{merged['code']}' already exists.", 400)
    merged["updated_at"] = datetime.now(timezone.utc)
    buildings_col().update_one({"_id": oid}, {"$set": merged})
    return ok(serialize(buildings_col().find_one({"_id": oid})))


@bp.route("/api/buildings/<bid>", methods=["DELETE"])
def delete_building(bid):
    oid = parse_object_id(bid)
    if oid is None:
        return fail("INVALID_ID", "Invalid building id.", 400)
    doc = buildings_col().find_one({"_id": oid})
    if not doc:
        return fail("NOT_FOUND", "Building not found.", 404)
    buildings_col().delete_one({"_id": oid})
    return ok({"message": "Building deleted.", "id": str(oid)})
