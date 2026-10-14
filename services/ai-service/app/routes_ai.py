"""AI endpoints: anomalies, forecast, recommendations, insights."""

from __future__ import annotations

import pandas as pd
from flask import Blueprint, jsonify, request

from app import analytics
from app.config import FORECAST_DEFAULT_DAYS, FORECAST_MAX_DAYS
from app.resource_client import ResourceServiceError, get_readings

ai_bp = Blueprint("ai", __name__)


def ok(data, status: int = 200):
    """Standard success envelope."""
    return jsonify({"success": True, "data": data}), status


def fail(message: str, status: int = 400):
    """Standard error envelope."""
    return jsonify({"success": False, "error": message}), status


def _get_limit(default: int = 200) -> int:
    raw = request.args.get("limit", default)
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        raise ValueError("Query param 'limit' must be an integer.")
    if limit < 1 or limit > 5000:
        raise ValueError("Query param 'limit' must be between 1 and 5000.")
    return limit


def _get_days() -> int:
    raw = request.args.get("days", FORECAST_DEFAULT_DAYS)
    try:
        days = int(raw)
    except (TypeError, ValueError):
        raise ValueError("Query param 'days' must be an integer.")
    if days < 1 or days > FORECAST_MAX_DAYS:
        raise ValueError(
            f"Query param 'days' must be between 1 and {FORECAST_MAX_DAYS}."
        )
    return days


def _fetch_readings(building_id=None, resource_type=None, limit: int = 200) -> list:
    """Fetch readings over HTTP; convert service errors to ValueError."""
    params: dict = {"limit": limit}
    if building_id:
        params["building_id"] = building_id
    if resource_type:
        params["resource_type"] = resource_type
    try:
        return get_readings(params)
    except ResourceServiceError as exc:
        raise ValueError(str(exc))


def _totals_for(readings: list) -> dict:
    if not readings:
        return {}
    df = pd.DataFrame(readings)
    if df.empty or "value" not in df.columns:
        return {}
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    if df.empty:
        return {}
    if "resource_type" in df.columns:
        grouped = df.groupby("resource_type")["value"].sum()
        return {str(k): round(float(v), 3) for k, v in grouped.items()}
    return {"total": round(float(df["value"].sum()), 3)}


# ------------------------------------------------------------------ #
@ai_bp.route("/anomalies", methods=["GET"])
def anomalies():
    """GET /api/ai/anomalies?building_id&resource_type&limit — z-score outliers."""
    try:
        limit = _get_limit()
    except ValueError as exc:
        return fail(str(exc), 400)
    building_id = request.args.get("building_id")
    resource_type = request.args.get("resource_type")
    try:
        readings = _fetch_readings(building_id, resource_type, limit)
    except ValueError as exc:
        return fail(str(exc), 502)

    result = analytics.detect_anomalies(readings)
    data = {
        "anomalies": result["anomalies"],
        "count": len(result["anomalies"]),
        "mean": result.get("mean"),
        "std": result.get("std"),
        "building_id": building_id,
        "resource_type": resource_type,
    }
    if result.get("message"):
        data["message"] = result["message"]
    return ok(data)


@ai_bp.route("/forecast", methods=["GET"])
def forecast():
    """GET /api/ai/forecast?building_id&resource_type&days=7 — trend forecast."""
    try:
        days = _get_days()
        limit = _get_limit(default=1000)
    except ValueError as exc:
        return fail(str(exc), 400)
    building_id = request.args.get("building_id")
    resource_type = request.args.get("resource_type")
    try:
        readings = _fetch_readings(building_id, resource_type, limit)
    except ValueError as exc:
        return fail(str(exc), 502)

    result = analytics.forecast_usage(readings, days=days)
    data = dict(result)
    data["building_id"] = building_id
    data["resource_type"] = resource_type
    data["days"] = days
    return ok(data)


@ai_bp.route("/recommendations", methods=["GET"])
def recommendations():
    """GET /api/ai/recommendations?building_id — rule-based saving tips."""
    building_id = request.args.get("building_id")
    try:
        limit = _get_limit(default=1000)
        readings = _fetch_readings(building_id, None, limit)
    except ValueError as exc:
        # Bad limit -> 400, service outage -> 502. Distinguish simply:
        msg = str(exc)
        status = 502 if ("HTTP" in msg or "reach" in msg or "timed out" in msg) else 400
        return fail(msg, status)

    totals = _totals_for(readings)
    anomaly_result = analytics.detect_anomalies(readings)
    recs = analytics.build_recommendations(totals, anomaly_result["anomalies"])
    return ok(
        {
            "recommendations": recs,
            "count": len(recs),
            "building_id": building_id,
            "totals": totals,
            "anomalies_count": len(anomaly_result["anomalies"]),
        }
    )


@ai_bp.route("/insights", methods=["GET"])
def insights():
    """GET /api/ai/insights?building_id — combined dashboard payload."""
    building_id = request.args.get("building_id")
    try:
        limit = _get_limit(default=1000)
        readings = _fetch_readings(building_id, None, limit)
    except ValueError as exc:
        msg = str(exc)
        status = 502 if ("HTTP" in msg or "reach" in msg or "timed out" in msg) else 400
        return fail(msg, status)

    totals = _totals_for(readings)
    anomaly_result = analytics.detect_anomalies(readings)
    anomalies = anomaly_result["anomalies"]
    forecast = analytics.forecast_usage(readings, days=7)
    recs = analytics.build_recommendations(totals, anomalies)
    costs = analytics.estimate_costs(totals)

    if readings:
        summary = (
            f"Analysed {len(readings)} reading(s)"
            + (f" for building '{building_id}'" if building_id else "")
            + f" across {len(totals)} resource type(s)."
        )
    else:
        summary = (
            "No readings available"
            + (f" for building '{building_id}'" if building_id else "")
            + ". Start logging data to unlock insights."
        )

    return ok(
        {
            "summary": summary,
            "building_id": building_id,
            "totals": totals,
            "readings_count": len(readings),
            "anomalies_count": len(anomalies),
            "anomalies": anomalies[:5],
            "forecast_preview": forecast.get("forecast", [])[:7],
            "forecast_method": forecast.get("method"),
            "forecast_is_estimate": forecast.get("is_estimate"),
            "recommendations": recs[:3],
            "cost_estimate": costs,
        }
    )
