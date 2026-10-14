# API Contracts — EcoPulse (Module 1, binding)

Base URLs: resource-service `http://localhost:5001`, ai-service `http://localhost:5002`.

## 1. Response envelope (binding for EVERY endpoint)

Success:

```json
{ "success": true, "data": {}, "error": null }
```

Failure (use proper HTTP status + this body):

```json
{ "success": false, "data": null, "error": { "code": "NOT_FOUND", "message": "Building not found" } }
```

Standard error codes: `VALIDATION_ERROR` (400), `INVALID_UNIT` (400), `NOT_FOUND` (404),
`CONFLICT` (409, e.g. duplicate building `code`), `UPSTREAM_ERROR` (502, ai-service only),
`INTERNAL_ERROR` (500).

## 2. resource-service (Flask, :5001)

### GET /api/health

Response `200`:

```json
{ "success": true, "data": { "status": "ok", "service": "resource-service" }, "error": null }
```

### Buildings

- `GET /api/buildings` → `200 { success, data: [Building], error }`
- `POST /api/buildings` — body: `{ name, code, type, floors, area_sqft, department?, location? }`

```json
// POST /api/buildings
{ "name": "CSE Block", "code": "CSE-BLK", "type": "academic", "floors": 4, "area_sqft": 25000, "department": "Computer Science", "location": "North Campus" }
// 201 → { "success": true, "data": { "Building...": "..." }, "error": null }
```

- `GET /api/buildings/<id>` → `200 Building` | `404 NOT_FOUND`
- `PUT /api/buildings/<id>` — body: any updatable subset (same fields as POST, `code` still unique) → `200 Building`
- `DELETE /api/buildings/<id>` → `200 { "deleted": true }` | `404 NOT_FOUND`

### Readings

- `GET /api/readings?building_id=&resource_type=&from=&to=&limit=`
  - Query (all optional): `building_id` (ObjectId str), `resource_type` (`electricity|water|waste`),
    `from` / `to` (ISO8601), `limit` (int, default 100, max 1000).
  - `200 { success, data: [Reading] (sorted by recorded_at asc), error }`
  - Example: `GET /api/readings?building_id=66f...&resource_type=electricity&limit=30`
- `POST /api/readings` — body:

```json
{
  "building_id": "66f1a2b3c4d5e6f708192a3b",
  "resource_type": "electricity",
  "value": 342.5,
  "unit": "kWh",
  "recorded_at": "2026-10-05T08:00:00Z",
  "source": "manual",
  "notes": "daily meter"
}
// 201 → { "success": true, "data": { "Reading with building_name denormalized": "..." }, "error": null }
```

Server sets `building_name` from the Building. Wrong unit → `400 INVALID_UNIT`.
Unknown `building_id` → `404 NOT_FOUND`.

- `GET /api/readings/<id>` → `200 Reading` | `404`
- `PUT /api/readings/<id>` — body subset `{ value?, unit?, recorded_at?, source?, notes? }` → `200 Reading`
- `DELETE /api/readings/<id>` → `200 { "deleted": true }`

### Dashboard

- `GET /api/dashboard/summary` → `200`:

```json
{
  "success": true,
  "data": {
    "totals": { "electricity_kwh": 12500.5, "water_l": 88000.0, "waste_kg": 1240.0 },
    "buildings_count": 6,
    "readings_count": 540,
    "open_issues": 4
  },
  "error": null
}
```

### Issues

- `GET /api/issues` → `200 [Issue]` (newest first; Modules 2+ may add `?status=` filter but MUST keep unfiltered default).
- `POST /api/issues` — body `{ title, description?, building_id?, category, priority?, reported_by? }` → `201 Issue` (status `open`).
- `PATCH /api/issues/<id>/status` — body `{ "status": "in_progress" }`
  (`status` ∈ `open|in_progress|resolved|closed`) → `200 Issue` with bumped `updated_at`. Bad value → `400 VALIDATION_ERROR`.

## 3. ai-service (Flask, :5002 — HTTP-only reads from resource-service)

### GET /api/health

```json
{ "success": true, "data": { "status": "ok", "service": "ai-service" }, "error": null }
```

If `RESOURCE_SERVICE_URL` unreachable, ai-service endpoints return `502`:

```json
{ "success": false, "data": null, "error": { "code": "UPSTREAM_ERROR", "message": "resource-service unreachable" } }
```

### GET /api/ai/anomalies?building_id=&resource_type=

```json
{
  "success": true,
  "data": {
    "anomalies": [
      { "recorded_at": "2026-10-05T08:00:00Z", "value": 900.0, "expected": 350.0, "severity": "high", "reason": "3.1x rolling mean" }
    ],
    "method": "rolling-mean + stddev"
  },
  "error": null
}
```

### GET /api/ai/forecast?building_id=&resource_type=&days=7

`days` default 7, clamp 1–30.

```json
{
  "success": true,
  "data": {
    "forecast": [
      { "date": "2026-10-15", "predicted_value": 360.2, "unit": "kWh" }
    ],
    "method": "moving-average"
  },
  "error": null
}
```

### GET /api/ai/recommendations?building_id=

```json
{
  "success": true,
  "data": {
    "recommendations": [
      { "title": "Fix corridor lighting", "detail": "Night-time baseload 40% above peers", "priority": "high", "category": "electricity" }
    ]
  },
  "error": null
}
```

### GET /api/ai/insights?building_id=

Combined view (totals + anomalies count + top recommendation). Shape fixed in Module 3 but MUST stay in envelope:

```json
{
  "success": true,
  "data": {
    "building_id": "66f...",
    "totals": { "electricity_kwh": 2400.0, "water_l": 15000.0, "waste_kg": 210.0 },
    "anomalies_count": 2,
    "trend": "increasing",
    "top_recommendation": { "title": "...", "priority": "high" }
  },
  "error": null
}
```

## 4. Contract test checklist (for Modules 2–5)

- Every response has `success/data/error` keys; `error` null on success.
- Unknown IDs → `404 NOT_FOUND` envelope. Bad enums → `400 VALIDATION_ERROR`.
- `GET /api/readings` respects `building_id/resource_type/from/to/limit`.
- ai-service with stopped resource-service → `502 UPSTREAM_ERROR` (not 500, not direct-DB error).
