# resource-service — EcoPulse system of record
Flask + MongoDB. Scaffolding only (Module 1); implementation lands in Module 2.

## Responsibilities (binding)

- Owns all MongoDB access (`DB_NAME=ecopulse_resource`).
- Serves buildings, readings, dashboard summary, issues.
- Responds with the shared envelope in `docs/api-contracts.md`.
- Allows CORS for the frontend origin (`http://localhost:3000` locally).

## Env

Copy `.env.example` to `.env`.

| Var | Example | Notes |
|-----|---------|-------|
| `MONGO_URI` | `mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority` | placeholder only |
| `DB_NAME` | `ecopulse_resource` | fixed |
| `PORT` | `5001` | fixed |

## Run (after Module 2)

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
python -m app.app
# GET http://localhost:5001/api/health
```
