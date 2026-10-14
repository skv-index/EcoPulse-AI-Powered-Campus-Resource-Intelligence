"""Dashboard endpoint: GET /api/dashboard/summary.

Viva: everything is computed in plain Python (no Mongo aggregation
pipeline) so the SAME code works on real MongoDB and on the in-memory
fallback. Window = last 30 days from now.
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint
from app import ok
from app.db import buildings_col, readings_col, issues_col

bp = Blueprint("dashboard", __name__)


@bp.route("/api/dashboard/summary", methods=["GET"])
def summary():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    buildings = list(buildings_col().find())
    readings = list(readings_col().find())
    issues = list(issues_col().find())

    def _aware(dt):
        # pymongo returns naive UTC datetimes; memory store keeps aware ones.
        if isinstance(dt, datetime) and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    recent = [r for r in readings
              if isinstance(r.get("recorded_at"), datetime)
              and _aware(r["recorded_at"]) >= cutoff]

    # 1) Totals by resource_type over the last 30 days.
    totals_30d = {"electricity": 0, "water": 0, "waste": 0}
    for r in recent:
        if r.get("resource_type") in totals_30d:
            totals_30d[r["resource_type"]] += r.get("value", 0) or 0

    # 2) Per-building totals (last 30 days) — used for bar charts.
    per_building = []
    for b in buildings:
        bid = str(b["_id"])
        mine = [r for r in recent if str(r.get("building_id")) == bid]
        per_building.append({
            "building_id": bid,
            "building_name": b.get("name", ""),
            "code": b.get("code", ""),
            "electricity": sum(r.get("value", 0) or 0 for r in mine
                               if r.get("resource_type") == "electricity"),
            "water": sum(r.get("value", 0) or 0 for r in mine
                         if r.get("resource_type") == "water"),
            "waste": sum(r.get("value", 0) or 0 for r in mine
                         if r.get("resource_type") == "waste"),
            "readings_count": len(mine),
        })
    per_building.sort(key=lambda x: x["building_name"])

    # 3) Simple counts.
    counts = {
        "buildings": len(buildings),
        "readings_total": len(readings),
        "readings_30d": len(recent),
        "issues_total": len(issues),
        "issues_open": sum(1 for i in issues if i.get("status") == "open"),
    }

    # 4) Issues grouped by status — used for the donut chart.
    issues_by_status = {"open": 0, "in_progress": 0, "resolved": 0, "closed": 0}
    for i in issues:
        if i.get("status") in issues_by_status:
            issues_by_status[i["status"]] += 1

    return ok({
        "totals_30d": totals_30d,
        "per_building": per_building,
        "counts": counts,
        "issues_by_status": issues_by_status,
        "window": {"from": cutoff.isoformat(), "to": now.isoformat(), "days": 30},
    })
