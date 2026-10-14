# ai-service — EcoPulse intelligence layer
Flask, stateless. Scaffolding only (Module 1); implementation lands in Module 3.

## Responsibilities (binding)

- NEVER connects directly to MongoDB (no `MONGO_URI`, no `DB_NAME`, no pymongo).
- Fetches readings via HTTP from `RESOURCE_SERVICE_URL` (resource-service).
- Serves anomalies, forecast, recommendations, insights.
- Allows CORS for the frontend origin (`http://localhost:3000` locally).

## Env

Copy `.env.example` to `.env`.

| Var | Example | Notes |
|-----|---------|-------|
| `RESOURCE_SERVICE_URL` | `http://localhost:5001` | resource-service base URL |
| `PORT` | `5002` | fixed |

## Run (after Module 3)

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
python -m app.app
# GET http://localhost:5002/api/health
```
