# EcoPulse — AI-Powered Campus Resource Intelligence

Sustainability dashboard for campus resource tracking (electricity, water, waste)
with anomaly detection, forecasting, and recommendations.

## Architecture (Module 1 — Shared Contracts + Scaffolding)

```
Browser (React, :3000)
   ├─> resource-service (Flask, :5001, MongoDB) — system of record
   └─> ai-service (Flask, :5002, stateless) — fetches readings via HTTP from resource-service, NEVER direct DB
```

> **No-direct-DB rule:** Only `resource-service` connects to MongoDB (`DB_NAME=ecopulse_resource`).
> `ai-service` MUST call `RESOURCE_SERVICE_URL` over HTTP.
> See `docs/architecture.md`. Contracts in `docs/api-contracts.md` + `docs/data-models.md` are binding for all later modules.

## Module status

| Module | Scope | Status |
|--------|-------|--------|
| 1 | Shared contracts, architecture, base scaffolding | ✅ Done (this commit) |
| 2 | resource-service implementation (Flask + MongoDB) | ⬜ Next |
| 3 | ai-service implementation (anomaly/forecast/recommend) | ⬜ Planned |
| 4 | Frontend dashboard (React) | ⬜ Planned |
| 5 | Seed data + integration + deployment | ⬜ Planned |

## Repo layout (Module 1 creates structure only — no implementation code yet)

```
frontend/src/{components,pages,layouts,services,hooks,utils}
services/resource-service/{app,tests}
services/ai-service/{app,tests}
docs/
```

## Prerequisites

- Python 3.10+
- Node 18+
- MongoDB Atlas account (free tier OK)

## MongoDB Atlas note

No real credentials are committed. Use placeholders only:

```
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

Create a cluster, add a DB user, and allow network access from `0.0.0.0/0` for Render hosting
(see `docs/deployment-guide.md`). Each developer copies `.env.example` to `.env` locally.

## Run instructions (after Modules 2–4 are implemented)

```powershell
# resource-service (:5001)
Copy-Item services\resource-service\.env.example services\resource-service\.env
pip install -r services\resource-service\requirements.txt
python -m app.app  # cwd: services/resource-service (actual entry point defined in Module 2)
```

```powershell
# ai-service (:5002)
Copy-Item services\ai-service\.env.example services\ai-service\.env
pip install -r services\ai-service\requirements.txt
python -m app.app  # cwd: services/ai-service (actual entry point defined in Module 3)
```

```powershell
# frontend (:3000)
Copy-Item frontend\.env.example frontend\.env
npm install  # cwd: frontend (package.json lands in Module 4)
npm start
```

Health checks (once implemented):

- `GET http://localhost:5001/api/health`
- `GET http://localhost:5002/api/health`

## Docs

- `docs/architecture.md` — diagram, responsibilities, ports, no-direct-DB rule
- `docs/api-contracts.md` — all endpoints + example req/res (binding)
- `docs/data-models.md` — Building / Reading / Issue schemas (binding)
- `docs/integration-guide.md` — how services call each other, CORS, env wiring
- `docs/testing-guide.md` — how Modules 2–5 will be tested
- `docs/deployment-guide.md` — Render (backends) + Vercel/Netlify (frontend), env tables, Atlas

## Next steps

1. Module 2: implement resource-service per `docs/api-contracts.md`.
2. Module 3: implement ai-service (HTTP-only reads from resource-service).
3. Module 4: build frontend against `REACT_APP_RESOURCE_URL` / `REACT_APP_AI_URL`.
4. Module 5: seed script, end-to-end tests, deploy.

---

## Final status (all modules complete)

| Module | Scope | Status |
|--------|-------|--------|
| 1 | Shared contracts, architecture, base scaffolding | ✅ Complete |
| 2 | resource-service implementation (Flask + MongoDB) | ✅ Complete (pytest 6/6) |
| 3 | ai-service implementation (anomaly/forecast/recommend) | ✅ Complete (pytest 15/15) |
| 4 | Frontend dashboard (React) | ✅ Complete |
| 5 | Seed data + integration + deployment docs | ✅ Complete |

Related docs: `docs/postman-collection.json`, `docs/integration-checklist.md`,
`docs/viva-notes.md` (plus `architecture.md`, `api-contracts.md`,
`data-models.md`, `integration-guide.md`, `testing-guide.md`, `deployment-guide.md`).

## How to run all 3 parts

Env setup (placeholders only — never commit real secrets):

```powershell
Copy-Item services\resource-service\.env.example services\resource-service\.env
Copy-Item services\ai-service\.env.example services\ai-service\.env
Copy-Item frontend\.env.example frontend\.env
# Edit each .env: MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority
# RESOURCE_SERVICE_URL=http://localhost:5001, REACT_APP_RESOURCE_URL=http://localhost:5001, REACT_APP_AI_URL=http://localhost:5002
```

```powershell
# 1. resource-service (:5001) — system of record
pip install -r services\resource-service\requirements.txt
python -m app.app  # cwd: services/resource-service
# check: GET http://localhost:5001/api/health
```

```powershell
# 2. ai-service (:5002) — stateless analytics, reads resource-service over HTTP
pip install -r services\ai-service\requirements.txt
python -m app.app  # cwd: services/ai-service
# check: GET http://localhost:5002/api/health
```

```powershell
# 3. frontend (:3000)
npm install  # cwd: frontend
npm start
```

| Part | Port | Health / entry |
|------|------|----------------|
| resource-service | 5001 | `GET /api/health` |
| ai-service | 5002 | `GET /api/health` |
| frontend | 3000 | `npm start` (uses `REACT_APP_RESOURCE_URL` / `REACT_APP_AI_URL`) |

## Integration results summary

- resource-service: **pytest 6/6 pass**; live `GET /api/health` OK.
- ai-service: **pytest 15/15 pass**; `get_summary` uses live `/api/dashboard/summary`.
- Inter-service: ai-service → resource-service **reachable=True** (HTTP only, no direct DB).
- `recorded_at` optional on `POST /api/readings` — defaults to now UTC.
- Forecast degrades gracefully (`is_estimate` fallback, never raw 500).
- All endpoints use `{ success, data, error }` envelope; CORS via `flask-cors`.
- Env-driven config; `ai-service/requirements.txt` has **no pymongo**.
- Full checklist: `docs/integration-checklist.md`.

## Deployment targets

- **Render** × 2 — `resource-service` and `ai-service` (one web service each,
  env vars set in Render dashboard, Atlas network access `0.0.0.0/0`).
- **Vercel** — frontend (`REACT_APP_RESOURCE_URL` / `REACT_APP_AI_URL`
  pointed at the live Render hosts).
- Details: `docs/deployment-guide.md`.

## Repo

https://github.com/skv-index/EcoPulse-AI-Powered-Campus-Resource-Intelligence.git

**Next steps: git push + deploy + point env URLs at the live hosts.**
