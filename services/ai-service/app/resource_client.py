"""HTTP client for the resource service.

CRITICAL RULE: this module is the ONLY way the AI service may access
measurements. It uses the ``requests`` library with a 10s timeout and
graceful errors. NEVER connect to MongoDB directly.
"""

from __future__ import annotations

import requests

from app.config import RESOURCE_SERVICE_TIMEOUT, RESOURCE_SERVICE_URL


class ResourceServiceError(Exception):
    """Raised when the resource service cannot provide data."""

    pass


def _base_url() -> str:
    return RESOURCE_SERVICE_URL.rstrip("/")


def _unwrap_list(payload, *candidate_keys: str) -> list:
    """Accept either a raw list or an envelope and return a plain list.

    The resource service normally responds with::

        {"success": True, "data": [...]}

    but some endpoints nest the list, e.g. ``{"data": {"readings": [...]}}``.
    This helper tolerates all of those shapes and returns [] for empties.
    """
    data = payload
    if isinstance(payload, dict):
        data = payload.get("data", payload)
    if isinstance(data, dict):
        for key in candidate_keys or ("readings", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
        # No recognisable list inside — treat as a single-object dict.
        return [data] if data else []
    if isinstance(data, list):
        return data
    return []


def _get(path: str, params: dict | None = None):
    """GET helper with timeout + graceful error messages."""
    url = f"{_base_url()}{path}"
    try:
        resp = requests.get(url, params=params or {}, timeout=RESOURCE_SERVICE_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        raise ResourceServiceError(
            f"Resource service timed out after {RESOURCE_SERVICE_TIMEOUT}s: {url}"
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise ResourceServiceError(
            f"Cannot reach resource service at {url}. "
            "Is it running? (default http://localhost:5001)"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ResourceServiceError(f"Request to {url} failed: {exc}") from exc

    if resp.status_code != 200:
        raise ResourceServiceError(
            f"Resource service returned HTTP {resp.status_code} for {url}: "
            f"{resp.text[:300]}"
        )
    try:
        return resp.json()
    except ValueError as exc:
        raise ResourceServiceError(
            f"Resource service returned non-JSON for {url}."
        ) from exc


def get_readings(params: dict | None = None) -> list:
    """Fetch readings via HTTP. ``params`` may hold building_id, resource_type, limit."""
    payload = _get("/api/readings", params=params or {})
    return _unwrap_list(payload, "readings", "items", "results", "data")


def get_buildings() -> list:
    """Fetch the building catalogue via HTTP."""
    payload = _get("/api/buildings")
    return _unwrap_list(payload, "buildings", "items", "results", "data")


def get_summary(building_id: str | None = None) -> dict:
    """Fetch aggregated summary via HTTP (falls back to {} when unavailable)."""
    params = {"building_id": building_id} if building_id else {}
    try:
        payload = _get("/api/dashboard/summary", params=params)
    except ResourceServiceError:
        return {}
    if isinstance(payload, dict):
        data = payload.get("data", payload)
        if isinstance(data, dict):
            return data
        return {"totals": data} if isinstance(data, list) else {}
    return {}


def ping() -> dict:
    """Lightweight reachability check used by /api/health. Never raises."""
    try:
        payload = _get("/api/health")
        if isinstance(payload, dict):
            return {"reachable": True, "detail": payload.get("data", payload)}
        return {"reachable": True, "detail": payload}
    except ResourceServiceError as exc:
        return {"reachable": False, "detail": str(exc)}
