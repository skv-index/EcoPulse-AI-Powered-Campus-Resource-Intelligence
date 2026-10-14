# Integration Guide — EcoPulse (Module 1)

## Service wiring

| From → To | How | Env var |
|-----------|-----|---------|
| ai-service → resource-service | `GET {RESOURCE_SERVICE_URL}/api/readings?building_id=..&resource_type=..&limit=500` via `requests` (timeout 10s) | `RESOURCE_SERVICE_URL` (default `http://localhost:5001`) |
| frontend → resource-service | `fetch(${REACT_APP_RESOURCE_URL}/api/buildings)` etc. | `REACT_APP_RESOURCE_URL` |
| frontend → ai-service | `fetch(${REACT_APP_AI_URL}/api/ai/forecast?...)` | `REACT_APP_AI_URL` |
| anyone → MongoDB | only resource-service via `pymongo` | `MONGO_URI`, `DB_NAME=ecopulse_resource` |

## Frontend service layer (Module 4 convention)

- `frontend/src/services/resourceApi.js` — buildings/readings/issues/dashboard calls.
- `frontend/src/services/aiApi.js` — anomalies/forecast/recommendations/insights calls.
- Both read base URLs from env, unwrap `{ success, data, error }`, and throw `Error(error.message)` when `success:false`.

## CORS

- Flask services use `flask-cors` open for the frontend origin.
- Local: `http://localhost:3000`. Deployed: Vercel/Netlify URL from `deployment-guide.md`.
- No credentials/cookies; plain JSON + standard verbs (`GET/POST/PUT/PATCH/DELETE`).

## Local bring-up order

1. Start MongoDB Atlas (connection string in `services/resource-service/.env`).
2. Start resource-service `:5001` → verify `GET /api/health`.
3. Start ai-service `:5002` with `RESOURCE_SERVICE_URL=http://localhost:5001` → verify `GET /api/health`.
4. Start frontend `:3000` → dashboard should load buildings + summary.

## Failure handling (binding)

- ai-service catches `requests.RequestException` → `502 UPSTREAM_ERROR` envelope (never leak tracebacks).
- Frontend shows a banner when either health check fails, with the failing base URL.
- resource-service validates `building_id` references and `unit`-matches-type before insert.
