"""pytest suite — covers health, building CRUD, reading CRUD+filters,
issue status patch, dashboard summary, and invalid-input 400s.

Run from services/resource-service:   py -m pytest -v
Uses the in-memory fallback (no MongoDB needed).
"""
import os

# Force the in-memory store BEFORE the app imports config/db.
os.environ["MONGO_URI"] = ""

import pytest  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

from app import create_app  # noqa: E402
from app.db import reset_memory_db  # noqa: E402


@pytest.fixture()
def client():
    reset_memory_db()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _make_building(client, code="CSE"):
    res = client.post("/api/buildings", json={
        "name": f"Block {code}", "code": code, "type": "academic",
        "floors": 3, "area_sqft": 10000,
        "department": "Test", "location": "Campus",
    })
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["error"] is None


def test_building_crud(client):
    b = _make_building(client)
    bid = b["_id"] if "_id" in b else b["id"]

    # list
    assert client.get("/api/buildings").get_json()["success"] is True

    # get one
    res = client.get(f"/api/buildings/{bid}")
    assert res.status_code == 200
    assert res.get_json()["data"]["code"] == "CSE"

    # update
    res = client.put(f"/api/buildings/{bid}", json={"floors": 5})
    assert res.status_code == 200
    assert res.get_json()["data"]["floors"] == 5

    # get missing -> 404 envelope
    res = client.get("/api/buildings/000000000000000000000000")
    assert res.status_code == 404
    assert res.get_json()["success"] is False

    # bad id -> 400 envelope
    res = client.get("/api/buildings/not-an-id")
    assert res.status_code == 400

    # delete
    res = client.delete(f"/api/buildings/{bid}")
    assert res.status_code == 200
    assert client.get(f"/api/buildings/{bid}").status_code == 404


def test_building_invalid_input_400(client):
    # missing name + bad type
    res = client.post("/api/buildings", json={"code": "X1", "type": "castle"})
    assert res.status_code == 400
    body = res.get_json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"

    # duplicate code
    _make_building(client, code="DUP")
    res = client.post("/api/buildings", json={
        "name": "Again", "code": "DUP", "type": "hostel"})
    assert res.status_code == 400


def test_reading_crud_and_filters(client):
    b = _make_building(client)
    bid = b["_id"] if "_id" in b else b["id"]
    now = datetime.now(timezone.utc).isoformat()

    def post_reading(rtype, unit, value):
        res = client.post("/api/readings", json={
            "building_id": bid, "resource_type": rtype,
            "value": value, "unit": unit, "recorded_at": now,
            "source": "test"})
        assert res.status_code == 201, res.get_json()
        return res.get_json()["data"]

    r1 = post_reading("electricity", "kWh", 150)
    post_reading("water", "L", 900)
    rid = r1["_id"] if "_id" in r1 else r1["id"]

    # get one / update / filter by type
    assert client.get(f"/api/readings/{rid}").status_code == 200
    res = client.put(f"/api/readings/{rid}", json={"value": 175})
    assert res.get_json()["data"]["value"] == 175

    res = client.get("/api/readings?resource_type=water")
    assert all(r["resource_type"] == "water" for r in res.get_json()["data"])

    res = client.get(f"/api/readings?building_id={bid}&limit=1")
    assert len(res.get_json()["data"]) == 1

    # bad value + bad unit -> 400
    res = client.post("/api/readings", json={
        "building_id": bid, "resource_type": "electricity",
        "value": -5, "unit": "kWh", "recorded_at": now})
    assert res.status_code == 400
    res = client.post("/api/readings", json={
        "building_id": bid, "resource_type": "electricity",
        "value": 10, "unit": "L", "recorded_at": now})
    assert res.status_code == 400

    # delete
    assert client.delete(f"/api/readings/{rid}").status_code == 200
    assert client.get(f"/api/readings/{rid}").status_code == 404


def test_issue_status_patch(client):
    b = _make_building(client)
    bid = b["_id"] if "_id" in b else b["id"]
    res = client.post("/api/issues", json={
        "title": "Leaky tap", "description": "Floor 2 washroom",
        "building_id": bid, "category": "water_leak",
        "priority": "high", "reported_by": "tester"})
    assert res.status_code == 201
    iid = res.get_json()["data"]["_id"]

    res = client.patch(f"/api/issues/{iid}/status", json={"status": "in_progress"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "in_progress"

    # invalid status -> 400
    res = client.patch(f"/api/issues/{iid}/status", json={"status": "flying"})
    assert res.status_code == 400

    # unknown issue -> 404
    res = client.patch("/api/issues/000000000000000000000000/status",
                       json={"status": "resolved"})
    assert res.status_code == 404


def test_dashboard_summary(client):
    b = _make_building(client)
    bid = b["_id"] if "_id" in b else b["id"]
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/readings", json={
        "building_id": bid, "resource_type": "electricity",
        "value": 100, "unit": "kWh", "recorded_at": now})
    client.post("/api/issues", json={
        "title": "Test issue", "building_id": bid, "category": "other"})

    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["totals_30d"]["electricity"] == 100
    assert data["counts"]["buildings"] == 1
    assert data["counts"]["issues_total"] == 1
    assert data["issues_by_status"]["open"] == 1
    assert isinstance(data["per_building"], list)
