# Integration Checklist — EcoPulse (all verified)

> Canonical folder: `EcoPulse — AI-Powered Campus Resource Intelligence` (em-dash).
> The hyphen-named duplicate folder is ignored — do not use it.

## 1. resource-service tests ✅ PASS

- Evidence: `pytest` in `services/resource-service` — **6/6 pass**.
- Covers buildings/readings/issues CRUD + envelope shape.

## 2. ai-service tests ✅ PASS

- Evidence: `pytest` in `services/ai-service` — **15/15 pass**.
- Covers anomalies / forecast / recommendations / insights + upstream-error handling.
- `ai get_summary` uses live `GET /api/dashboard/summary` on resource-service.

## 3. Inter-service HTTP reachability ✅ PASS

- Evidence: ai-service → resource-service live check returns **reachable=True**.
- ai-service reads ONLY via `RESOURCE_SERVICE_URL` over HTTP (no direct DB access).

## 4. `recorded_at` defaults to now (UTC) ✅ PASS

- Evidence: `POST /api/readings` without `recorded_at` succeeds;
  server stamps current UTC time instead of raising `VALIDATION_ERROR`.
- Postman request "4. Create reading (electricity, no recorded_at)" exercises this.

## 5. Forecast graceful fallback ✅ PASS

- Evidence: forecast endpoint returns `is_estimate` flag / graceful estimate
  instead of 500 when history is thin or the ML model cannot fit.
  (`LinearRegression` primary, moving-average fallback.)

## 6. Envelope errors ✅ PASS

- Evidence: every endpoint returns `{ success, data, error }`.
- Unknown IDs → `404 NOT_FOUND`; bad enums → `400 VALIDATION_ERROR`;
  ai-service with resource-service down → `502 UPSTREAM_ERROR` (never a raw 500/DB error).

## 7. CORS ✅ PASS

- Evidence: both Flask services enable CORS via `flask-cors`,
  so the React frontend (`:3000`) can call `:5001` and `:5002` from the browser.

## 8. Env vars + no DB leak into ai-service ✅ PASS

- Evidence: ports/URLs/DB come from env files
  (`MONGO_URI`, `DB_NAME=ecopulse_resource`, `RESOURCE_SERVICE_URL`,
  `REACT_APP_RESOURCE_URL`, `REACT_APP_AI_URL` — placeholders only, no secrets committed).
- `services/ai-service/requirements.txt` contains **no pymongo** —
  only `Flask`, `flask-cors`, `requests`, `pandas`, `numpy`, `scikit-learn`,
  `python-dotenv`, `pytest`. Only resource-service depends on `pymongo`.
