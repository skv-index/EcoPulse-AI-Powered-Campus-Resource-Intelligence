# Viva Notes — EcoPulse (short Q&A)

## 1. What is the microservices split?

- **resource-service** (Flask, :5001, MongoDB) — system of record:
  buildings, readings, issues, dashboard summary.
- **ai-service** (Flask, :5002, stateless) — analytics only:
  anomalies, forecast, recommendations, insights.
- **frontend** (React, :3000) — dashboard calling both APIs.
- Each service runs, deploys, and scales independently.

## 2. Why does ai-service use HTTP instead of direct DB access?

- Single-owner rule: only resource-service owns the database
  (`DB_NAME=ecopulse_resource`), so schema/validation lives in one place.
- ai-service fetches readings via `RESOURCE_SERVICE_URL` over HTTP.
  Proof: `ai-service/requirements.txt` has **no pymongo**.
- If resource-service is down, ai-service returns `502 UPSTREAM_ERROR`
  instead of crashing — failure is explicit and testable.

## 3. What is the response envelope?

- Every endpoint returns `{ success, data, error }`.
- Success: `{ "success": true, "data": {...}, "error": null }`.
- Failure: `{ "success": false, "data": null,
  "error": { "code": "NOT_FOUND", "message": "..." } }`
  with the matching HTTP status (400/404/409/502/500).
- Standard codes: `VALIDATION_ERROR`, `INVALID_UNIT`, `NOT_FOUND`,
  `CONFLICT`, `UPSTREAM_ERROR`, `INTERNAL_ERROR`.

## 4. What CRUD does resource-service expose?

- Buildings: `GET/POST /api/buildings`, `GET/PUT/DELETE /api/buildings/<id>`
  (`code` unique → `409 CONFLICT` on duplicates).
- Readings: `GET/POST /api/readings` (filters: `building_id`,
  `resource_type`, `from`, `to`, `limit`; `recorded_at` optional,
  defaults to now UTC), plus `GET/PUT/DELETE /api/readings/<id>`.
- Issues: `GET/POST /api/issues`, `PATCH /api/issues/<id>/status`
  (`open → in_progress → resolved → closed`).
- Dashboard: `GET /api/dashboard/summary` (totals + counts + open issues).

## 5. How does anomaly detection work?

- Z-score / rolling-mean + standard-deviation method.
- For each reading, compare `value` against a rolling mean of prior points;
  flag when deviation exceeds *k* standard deviations
  (e.g. value 900 vs expected 350 → severity `high`).
- Response includes `value`, `expected`, `severity`, `reason`, and `method`.

## 6. How does forecasting work?

- Primary: `LinearRegression` (scikit-learn) on time-indexed history.
- Fallback: moving-average when history is too short or fitting fails —
  the response flags this with `is_estimate` instead of returning 500.
- Query clamps `days` to 1–30 (default 7).

## 7. What does CORS do here?

- Browsers block cross-origin calls by default; the React app (:3000)
  calls APIs on :5001/:5002, which are different origins.
- Both Flask services use `flask-cors` to send
  `Access-Control-Allow-Origin`, so the dashboard works in the browser.

## 8. Which env vars matter?

- resource-service: `MONGO_URI` (placeholder only),
  `DB_NAME=ecopulse_resource`, `PORT=5001`.
- ai-service: `RESOURCE_SERVICE_URL` (points at resource-service),
  `PORT=5002`.
- frontend: `REACT_APP_RESOURCE_URL`, `REACT_APP_AI_URL`.
- Rule: copy `.env.example` → `.env`; **never commit real secrets**.

## 9. How is it deployed?

- 2 backends → **Render** (one web service per Flask app,
  env vars set in the Render dashboard, Atlas allow-list `0.0.0.0/0`).
- Frontend → **Vercel** (`REACT_APP_*` URLs pointed at the Render hosts).
- Repo: https://github.com/skv-index/EcoPulse-AI-Powered-Campus-Resource-Intelligence.git
- Next steps: `git push` + deploy + point env URLs at the live hosts.
