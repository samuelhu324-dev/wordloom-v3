# ADR-066: RULES Sync + Runtime Standardization (Ports, Proxy, Prefix)

- Date: 2025-11-17
- Status: Accepted
- Owner: Frontend/Backend Integration
- Supersedes: ADR-064 (prefix alignment to /api) — superseded by ADR-065 and this ADR
- Related: ADR-063 (Same-origin proxy), ADR-065 (prefix correction to /api/v1), ADR-054 (API bootstrap), ADR-053 (Database schema)

## Context
During API integration, the frontend and backend used inconsistent ports and an incorrect health path:
- Frontend dev server runs on 30001.
- Backend API should run on 30002.
- Actual backend router prefix is `/api/v1` (confirmed in `backend/api/app/main.py`).
- Multiple RULES documents still referenced 30001 for the backend and `/api` as the prefix.
- Health checks in docs pointed to `/health` instead of `/api/v1/health`.

This caused confusion, 404/500 errors during integration, and mismatched documentation.

## Decision
Standardize local development runtime and synchronize documentation across RULES files.

- Frontend: Next.js on `http://localhost:30001`.
- Backend: FastAPI (Uvicorn) on `http://localhost:30002`.
- API Prefix: `/api/v1`.
- Same-origin Proxy: Next rewrites all requests matching `/api/v1/:path*` to `http://localhost:30002/api/v1/:path*`.
- Health Endpoint: `GET http://localhost:30002/api/v1/health`.

## Implementation
- Updated RULES documents to reflect the final configuration:
  - `assets/docs/HEXAGONAL_RULES.yaml`
    - `api_server_port: 30002`, `api_server_url: http://localhost:30002`, `api_prefix: /api/v1`.
    - Health check updated to `/api/v1/health`.
    - `latest_adr` set to this ADR.
  - `assets/docs/VISUAL_RULES.yaml`
    - `api_server_details.health_endpoint` → `/api/v1/health`.
    - `api_routers_available` updated to `/api/v1/*`.
    - `api_connection_status` clarified: backend expected on 30002 via rewrites.
  - `assets/docs/DDD_RULES.yaml`
    - Frontend port corrected to 30001; backend to 30002.
    - `api_prefix: /api/v1`; health endpoint corrected; router list uses `/api/v1/*`.

- Environment variables (frontend):
  - `NEXT_PUBLIC_API_BASE=http://localhost:30001`
  - `NEXT_PUBLIC_API_PREFIX=/api/v1`
  - `API_PROXY_TARGET=http://localhost:30002`
  - `API_PROXY_PREFIX=/api/v1`
  - `NEXT_PUBLIC_USE_MOCK=0`

- Next.js rewrite (concept):
  - `${API_PROXY_PREFIX}/:path*` → `${API_PROXY_TARGET}${API_PROXY_PREFIX}/:path*`.

## Verification
- Backend started with:
  - `uvicorn api.app.main:app --host 127.0.0.1 --port 30002 --reload`
- Health check returns 200:
  - `GET http://localhost:30002/api/v1/health`
- Frontend served at 30001; visiting `/admin/libraries` triggers:
  - `GET http://localhost:30001/api/v1/libraries` (proxied to 30002).

## Consequences
- Single source of truth for ports/prefix across RULES files.
- Reduced 404/500s caused by mismatched prefixes or ports.
- Clear runbook for local development and CI.

## Rollback
- If backend must run on 30001, set `API_PROXY_TARGET` to `http://localhost:30001` and keep `API_PROXY_PREFIX=/api/v1`.
- No code changes needed on the frontend beyond env/rewrites.

## Next Steps
- Ensure `backend` service listens on 30002 in local `.env`/compose.
- Add CI check to validate RULES docs consistency (simple grep for `/api/v1` + 30002).
- Continue end-to-end testing for Libraries feature and expand to other domains.
