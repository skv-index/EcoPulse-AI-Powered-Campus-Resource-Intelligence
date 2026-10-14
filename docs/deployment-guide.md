# Deployment Guide — EcoPulse (Module 1 plan; executed in Module 5)

## Targets

| Component | Host | Build / start |
|-----------|------|---------------|
| resource-service | Render (Web Service, Python) | build `pip install -r requirements.txt`; start `gunicorn wsgi:app --bind 0.0.0.0:$PORT` (Root Directory `services/resource-service`) |
| ai-service | Render (Web Service, Python) | build `pip install -r requirements.txt`; start `gunicorn wsgi:app --bind 0.0.0.0:$PORT` (Root Directory `services/ai-service`) |
| frontend | Vercel or Netlify | build `npm run build` (cwd `frontend`); output `build/` |

## Env tables (set in host dashboards, never commit)

### resource-service (Render)

| Var | Value |
|-----|-------|
| `MONGO_URI` | `mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority` |
| `DB_NAME` | `ecopulse_resource` |

> ⚠️ Do NOT set `PORT` on Render — Render injects its own `PORT` and the
> start command (`gunicorn wsgi:app --bind 0.0.0.0:$PORT`) already uses it.
> Hardcoding `PORT=5001` makes gunicorn bind the wrong port and the service
> returns 502. (`PORT=5001`/`5002` belong only in local `.env` files.)

### ai-service (Render)

| Var | Value |
|-----|-------|
| `RESOURCE_SERVICE_URL` | `https://<resource-service>.onrender.com` (no trailing slash) |

(Same `PORT` rule: do not set it on Render.)

### frontend (Vercel/Netlify)

| Var | Value |
|-----|-------|
| `REACT_APP_RESOURCE_URL` | `https://<resource-service>.onrender.com` |
| `REACT_APP_AI_URL` | `https://<ai-service>.onrender.com` |

## CORS

- After frontend URL is known, confirm both Flask apps allow it
  (`flask-cors` open for that origin). Local dev keeps `http://localhost:3000`.
- Test: browser devtools fetch to `/api/health` from deployed frontend → 200, no CORS error.

## MongoDB Atlas

- Free M0 cluster; DB user with read/write on `ecopulse_resource`.
- Network Access → Allow from anywhere `0.0.0.0/0` (required for Render).
- Only placeholder URIs in docs/`.env.example`; real URI pasted in Render dashboard.

## Deploy order + verify

1. Deploy resource-service → `GET https://<rs>/api/health` → 200.
2. Deploy ai-service with `RESOURCE_SERVICE_URL` → `GET https://<ai>/api/health` → 200,
   then `GET https://<ai>/api/ai/insights?building_id=<seed-id>` → 200 (or `502` only if RS down).
3. Deploy frontend with both `REACT_APP_*` URLs → dashboard loads, no console CORS errors.
