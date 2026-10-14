"""Unit + API tests for the AI microservice.

Run from the ai-service folder:  pytest -q
We mock app.resource_client (HTTP layer) with monkeypatch, so no
resource service or MongoDB is needed.
"""

import sys
import os
from datetime import datetime, timedelta

import pandas as pd
import pytest

# Make `app` importable when pytest runs from the service root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import analytics, create_app  # noqa: E402


# ---------- helpers -------------------------------------------------- #
def _readings(values, building_id="B1", resource_type="electricity", start="2026-01-01"):
    base = datetime.fromisoformat(start)
    return [
        {
            "reading_id": f"r{i}",
            "building_id": building_id,
            "resource_type": resource_type,
            "value": v,
            "unit": "kWh",
            "recorded_at": (base + timedelta(hours=i)).isoformat(),
        }
        for i, v in enumerate(values)
    ]


def _daily_readings(n_days, per_day=10.0, slope=0.0, resource_type="electricity"):
    base = datetime(2026, 1, 1)
    out = []
    for d in range(n_days):
        out.append(
            {
                "reading_id": f"d{d}",
                "building_id": "B1",
                "resource_type": resource_type,
                "value": per_day + slope * d,
                "unit": "kWh",
                "recorded_at": (base + timedelta(days=d)).isoformat(),
            }
        )
    return out


# ---------- anomaly detection --------------------------------------- #
def test_anomaly_detects_synthetic_spike():
    values = [10.0] * 20 + [100.0]  # one obvious spike
    result = analytics.detect_anomalies(_readings(values))
    assert result["message"] is None or result["anomalies"]
    assert len(result["anomalies"]) >= 1
    top = result["anomalies"][0]
    assert top["value"] == 100.0
    assert abs(top["z_score"]) > 2.5
    assert top["expected_range"][0] < top["expected_range"][1]
    assert top["severity"] in ("medium", "high", "critical")
    for key in ("reading_id", "building_id", "resource_type", "value",
                "expected_range", "z_score", "recorded_at", "severity"):
        assert key in top


def test_anomaly_insufficient_data():
    result = analytics.detect_anomalies(_readings([1, 2, 3]))
    assert result["anomalies"] == []
    assert "insufficient data" in result["message"]


def test_anomaly_empty_input():
    result = analytics.detect_anomalies([])
    assert result["anomalies"] == []
    assert "insufficient data" in result["message"]


# ---------- forecasting --------------------------------------------- #
def test_forecast_linear_trend():
    readings = _daily_readings(14, per_day=10.0, slope=2.0)
    result = analytics.forecast_usage(readings, days=7)
    assert result["method"] == "linear_regression"
    assert result["is_estimate"] is False
    assert len(result["history"]) == 14
    assert len(result["forecast"]) == 7
    preds = [f["predicted_value"] for f in result["forecast"]]
    assert preds == sorted(preds)  # upward trend continues
    assert all("date" in f and "predicted_value" in f and "unit" in f
               for f in result["forecast"])


def test_forecast_insufficient_data_fallback():
    readings = _daily_readings(3, per_day=10.0)
    result = analytics.forecast_usage(readings, days=7)
    assert result["is_estimate"] is True
    assert result["method"] == "naive_average"
    assert len(result["forecast"]) == 7
    assert "insufficient data" in result["message"].lower()
    assert "disclaimer" in result


def test_forecast_empty():
    result = analytics.forecast_usage([], days=7)
    assert result["is_estimate"] is True
    assert result["forecast"] == []


# ---------- recommendations + costs --------------------------------- #
def test_recommendations_rules():
    totals = {"electricity": 5000, "water": 9000, "waste": 800}
    anomalies = [{"resource_type": "water", "z_score": 3.5}]
    recs = analytics.build_recommendations(totals, anomalies)
    cats = {r["category"] for r in recs}
    assert {"electricity", "water", "waste"} <= cats
    for r in recs:
        for key in ("title", "description", "category",
                    "potential_saving_pct", "priority"):
            assert key in r


def test_recommendations_empty_graceful():
    recs = analytics.build_recommendations({}, [])
    assert len(recs) >= 1


def test_estimate_costs_rates():
    costs = analytics.estimate_costs(
        {"electricity": 100, "water": 1000, "waste": 50}
    )
    assert costs["breakdown"]["electricity"] == pytest.approx(800.0)
    assert costs["breakdown"]["water"] == pytest.approx(60.0)
    assert costs["breakdown"]["waste"] == pytest.approx(100.0)
    assert costs["total"] == pytest.approx(960.0)
    assert costs["currency"] == "INR"


# ---------- API layer (mocked HTTP client) --------------------------- #
@pytest.fixture()
def client(monkeypatch):
    import app.routes_ai as routes

    monkeypatch.setattr(
        routes, "get_readings",
        lambda params=None: _daily_readings(14, per_day=10.0, slope=1.0),
    )
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    return flask_app.test_client()


def test_api_health():
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    c = flask_app.test_client()
    resp = c.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["service"] == "ai-service"
    assert "resource_service" in body["data"]
    assert "timestamp" in body["data"]


def test_api_anomalies_endpoint(client):
    resp = client.get("/api/ai/anomalies?building_id=B1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "anomalies" in body["data"]


def test_api_anomalies_insufficient(client, monkeypatch):
    import app.routes_ai as routes

    monkeypatch.setattr(routes, "get_readings", lambda params=None: [])
    resp = client.get("/api/ai/anomalies")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["anomalies"] == []


def test_api_forecast_validation(client):
    resp = client.get("/api/ai/forecast?days=99")
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_api_forecast_ok(client):
    resp = client.get("/api/ai/forecast?building_id=B1&days=7")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data["forecast"]) == 7
    assert "disclaimer" in data


def test_api_recommendations_and_insights(client):
    rec = client.get("/api/ai/recommendations?building_id=B1")
    assert rec.status_code == 200
    assert "recommendations" in rec.get_json()["data"]

    ins = client.get("/api/ai/insights?building_id=B1")
    assert ins.status_code == 200
    data = ins.get_json()["data"]
    for key in ("summary", "totals", "anomalies_count",
                "forecast_preview", "recommendations", "cost_estimate"):
        assert key in data
    assert data["cost_estimate"]["currency"] == "INR"
