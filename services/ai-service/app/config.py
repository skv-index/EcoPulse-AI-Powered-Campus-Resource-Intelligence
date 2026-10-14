"""Central configuration for the AI microservice.

Beginner note: everything comes from environment variables so the
service works locally and in containers without code changes.
Never put secrets in this file — see .env.example.
"""

import os


def _get_port() -> int:
    """Read PORT from the environment, defaulting to 5002."""
    try:
        return int(os.getenv("PORT", "5002"))
    except (TypeError, ValueError):
        return 5002


PORT: int = _get_port()

# Base URL of the resource service. CRITICAL: all readings MUST come
# from here over HTTP. Never connect to MongoDB directly.
RESOURCE_SERVICE_URL: str = os.getenv(
    "RESOURCE_SERVICE_URL", "http://localhost:5001"
).rstrip("/")

# HTTP timeout (seconds) for calls to the resource service.
RESOURCE_SERVICE_TIMEOUT: int = 10

# Analytics tuning knobs (kept here so beginners can tweak safely).
ANOMALY_Z_THRESHOLD: float = 2.5
ANOMALY_MIN_POINTS: int = 10
FORECAST_MIN_DAYS: int = 7
FORECAST_DEFAULT_DAYS: int = 7
FORECAST_MAX_DAYS: int = 30
