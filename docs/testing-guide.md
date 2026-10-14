# Testing Guide — EcoPulse (Module 1; executed in Modules 2–5)

## Backend (pytest, per service)

```powershell
# from services/resource-service or services/ai-service
pip install -r requirements.txt
pytest -q
```

### resource-service (Module 2 must pass)

- `test_health` — `GET /api/health` → 200 envelope.
- Building CRUD: create → get → put → delete; duplicate `code` → 409; bad `type` → 400.
- Reading CRUD: create with denormalized `building_name`; wrong unit → 400 `INVALID_UNIT`;
  unknown building → 404; `GET /api/readings` filters (`building_id`, `resource_type`, `from/to`, `limit`).
- Dashboard: `GET /api/dashboard/summary` has `totals/buildings_count/readings_count/open_issues`.
- Issues: create defaults `status=open`; `PATCH /status` transitions + bad value → 400.
- Envelope: every response has `success/data/error`.

### ai-service (Module 3 must pass; mock resource-service with `responses`/`monkeypatch`)

- `test_health`, plus each `/api/ai/*` happy path with mocked readings.
- Upstream-down test: resource-service down → `502 UPSTREAM_ERROR` envelope.
- No `pymongo` import and no `MONGO_URI` usage (grep check).
- Forecast length == `days` param (clamped 1–30).

## Frontend (Module 4)

- `npm test` / manual: dashboard renders with mocked API; bad-base-URL shows error banner.
- Verify no hardcoded `localhost:5001` in `src/` (only via `REACT_APP_*`).

## E2E (Module 5)

1. Seed DB → resource `:5001` up → ai `:5002` up → frontend `:3000` up.
2. Create building → post readings → anomalies/forecast return non-empty.
3. Report issue → status PATCH → dashboard `open_issues` decrements.
