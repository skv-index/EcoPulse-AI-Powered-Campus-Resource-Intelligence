"""Central config — reads everything from environment variables.

Viva: Flask never hard-codes secrets. MONGO_URI / DB_NAME / PORT all come
from the environment (or a local .env file), with safe demo defaults.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()  # picks up services/resource-service/.env for any entry point
except ImportError:  # pragma: no cover - dotenv optional
    pass


MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "ecopulse_resource")
PORT = int(os.getenv("PORT", "5001"))
