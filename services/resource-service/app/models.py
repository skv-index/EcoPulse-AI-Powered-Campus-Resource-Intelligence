"""Validation helpers — each returns (ok: bool, errors: dict).

Viva: routes call validate_* BEFORE touching the DB. If ok is False the
route returns HTTP 400 with the envelope error; the `errors` dict tells
the client exactly which field failed.
"""
from datetime import datetime


BUILDING_TYPES = {"academic", "hostel", "admin", "lab", "canteen"}
RESOURCE_TYPES = {"electricity", "water", "waste"}
UNITS = {"kWh", "L", "kg"}
# Expected unit per resource type (keeps demo data consistent).
RESOURCE_UNIT = {"electricity": "kWh", "water": "L", "waste": "kg"}
ISSUE_CATEGORIES = {"water_leak", "faulty_light", "overflowing_bin", "hvac", "other"}
ISSUE_PRIORITIES = {"low", "medium", "high", "critical"}
ISSUE_STATUSES = {"open", "in_progress", "resolved", "closed"}


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_building(data):
    """Required: name, code, type. Optional: floors, area_sqft, dept, location."""
    errors = {}
    if not isinstance(data, dict):
        return False, {"body": "Request body must be a JSON object."}
    if not str(data.get("name", "")).strip():
        errors["name"] = "name is required."
    if not str(data.get("code", "")).strip():
        errors["code"] = "code is required (must be unique)."
    if data.get("type") not in BUILDING_TYPES:
        errors["type"] = f"type must be one of {sorted(BUILDING_TYPES)}."
    if "floors" in data and data["floors"] is not None:
        if not isinstance(data["floors"], int) or isinstance(data["floors"], bool) \
                or data["floors"] < 0:
            errors["floors"] = "floors must be an integer >= 0."
    if "area_sqft" in data and data["area_sqft"] is not None:
        if not _is_number(data["area_sqft"]) or data["area_sqft"] < 0:
            errors["area_sqft"] = "area_sqft must be a number >= 0."
    return (len(errors) == 0), errors


def validate_reading(data):
    """Required: building_id, resource_type, value>=0, unit, recorded_at ISO8601."""
    errors = {}
    if not isinstance(data, dict):
        return False, {"body": "Request body must be a JSON object."}
    if not str(data.get("building_id", "")).strip():
        errors["building_id"] = "building_id is required."
    if data.get("resource_type") not in RESOURCE_TYPES:
        errors["resource_type"] = f"resource_type must be one of {sorted(RESOURCE_TYPES)}."
    if not _is_number(data.get("value")) or data["value"] < 0:
        errors["value"] = "value must be a number >= 0."
    if data.get("unit") not in UNITS:
        errors["unit"] = f"unit must be one of {sorted(UNITS)}."
    elif (data.get("resource_type") in RESOURCE_UNIT
            and data.get("unit") != RESOURCE_UNIT[data["resource_type"]]):
        errors["unit"] = (
            f"unit for {data.get('resource_type')} should be "
            f"'{RESOURCE_UNIT[data['resource_type']]}'."
        )
    rec = data.get("recorded_at")
    if rec is None or (isinstance(rec, str) and not rec.strip()):
        pass  # optional — route defaults to now (UTC)
    elif not isinstance(rec, str):
        errors["recorded_at"] = "recorded_at must be ISO8601, e.g. 2026-10-01T10:00:00Z."
    else:
        try:
            datetime.fromisoformat(rec.replace("Z", "+00:00"))
        except ValueError:
            errors["recorded_at"] = "recorded_at must be ISO8601, e.g. 2026-10-01T10:00:00Z."
    return (len(errors) == 0), errors


def validate_issue(data):
    """Required: title, building_id, category. Defaults: priority, status."""
    errors = {}
    if not isinstance(data, dict):
        return False, {"body": "Request body must be a JSON object."}
    if not str(data.get("title", "")).strip():
        errors["title"] = "title is required."
    if not str(data.get("building_id", "")).strip():
        errors["building_id"] = "building_id is required."
    if data.get("category") not in ISSUE_CATEGORIES:
        errors["category"] = f"category must be one of {sorted(ISSUE_CATEGORIES)}."
    if "priority" in data and data["priority"] not in ISSUE_PRIORITIES:
        errors["priority"] = f"priority must be one of {sorted(ISSUE_PRIORITIES)}."
    if "status" in data and data["status"] not in ISSUE_STATUSES:
        errors["status"] = f"status must be one of {sorted(ISSUE_STATUSES)}."
    return (len(errors) == 0), errors


def validate_status_transition(value):
    """Used by PATCH /api/issues/<id>/status — body is just {"status": ...}."""
    if value not in ISSUE_STATUSES:
        return False, {"status": f"status must be one of {sorted(ISSUE_STATUSES)}."}
    return True, {}
