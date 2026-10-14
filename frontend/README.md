# EcoPulse Frontend (Module 4)

React 18 dashboard for **EcoPulse — AI-Powered Campus Resource Intelligence**.

## Structure (binding, from Module 1)

```
frontend/src/
  components/  # reusable UI (StatCard, KpiCard, Chart, DataTable, badges, states)
  pages/       # route-level views (Dashboard, Analytics, Buildings, AIInsights, Issues, Reports)
  layouts/     # App shell + sidebar nav (MainLayout)
  services/    # API clients for resource-service + ai-service (api.js)
  hooks/       # custom React hooks (useFetch)
  utils/       # formatters (format.js), sample fallback data (sampleData.js)
```

## Setup

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm start  # http://localhost:3000
```

## Env

Copy `.env.example` to `.env`. Never commit `.env`. No DB credentials live here.

| Var | Example | Notes |
|-----|---------|-------|
| `REACT_APP_RESOURCE_URL` | `http://localhost:5001` | resource-service base URL |
| `REACT_APP_AI_URL` | `http://localhost:5002` | ai-service base URL |

## Scripts

- `npm start` — dev server (port 3000)
- `npm run build` — production build
- `npm test` — CRA tests

## API client

Centralized in `src/services/api.js` (axios):
`api.get/post/put/patch/del` -> resource-service,
`api.ai.get/...` -> ai-service.
Envelope unwrapping (`data`/`result`/`items`), 10s timeout, normalized errors.

## Demo mode

Every page reads **only** from the API. If the API is down, the page shows:

1. an `ErrorState` with the error + Retry, and
2. a yellow **SAMPLE — demo mode** banner with clearly-labeled sample data
   from `src/utils/sampleData.js`.
