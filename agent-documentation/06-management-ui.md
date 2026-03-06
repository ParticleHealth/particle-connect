# Management UI

Dockerized admin interface for the Particle Health Management API. Located in `management-ui/`.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  React Frontend │────▶│  FastAPI Backend  │────▶│  Particle Health     │
│  (nginx :3000)  │     │  (proxy :8000)    │     │  Management API      │
└─────────────────┘     └──────────────────┘     └──────────────────────┘
```

- **Frontend**: React 19 + TypeScript, built with Vite, served by nginx on port 3000
- **Backend**: FastAPI, proxies all requests to Particle Management API, caches JWT in-memory
- **No database**: All state comes from Particle's API

## Backend Structure

```
backend/
  app/
    main.py                      # FastAPI app, CORS, lifespan, router registration
    config.py                    # Settings (BaseSettings from .env)
    services/
      particle_client.py         # ParticleClient singleton — async HTTP + JWT management
    routers/
      auth.py                    # POST /api/auth/connect, GET /api/auth/status, POST /api/auth/switch
      projects.py                # GET/POST /api/projects, GET/PATCH /api/projects/{id}
      service_accounts.py        # GET/POST /api/service-accounts, GET /api/service-accounts/{id}
      credentials.py             # POST/GET/DELETE /api/service-accounts/{id}/credentials
      notifications.py           # CRUD for webhook notification configs + signature keys
```

### Backend API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/auth/connect` | POST | Authenticate using .env credentials |
| `/api/auth/status` | GET | Check if backend holds valid JWT |
| `/api/auth/switch` | POST | Switch between sandbox/production |
| `/api/health` | GET | Health check with auth status |
| `/api/projects` | GET | List all projects |
| `/api/projects` | POST | Create new project |
| `/api/projects/{id}` | GET | Get project details |
| `/api/projects/{id}` | PATCH | Update project (activate/deactivate) |
| `/api/service-accounts` | GET | List service accounts |
| `/api/service-accounts` | POST | Create service account |
| `/api/service-accounts/{id}` | GET | Get service account details |
| `/api/service-accounts/{id}/policy` | POST | Set IAM policy |
| `/api/service-accounts/{id}/policy` | GET | Get IAM policy |
| `/api/service-accounts/{id}/credentials` | POST | Create credential (secret shown once) |
| `/api/service-accounts/{id}/credentials` | GET | List credentials |
| `/api/service-accounts/{id}/credentials/{cid}` | DELETE | Delete credential |
| `/api/notifications` | GET | List webhook notification configs |
| `/api/notifications` | POST | Create notification config |
| `/api/notifications/{id}` | GET | Get notification config |
| `/api/notifications/{id}` | PATCH | Update notification (callback_url, active status) |
| `/api/notifications/{id}` | DELETE | Delete notification config |
| `/api/notifications/{id}/signaturekeys` | POST | Create signature key for webhook verification |
| `/api/notifications/{id}/signaturekeys/{kid}` | GET | Get signature key |
| `/api/notifications/{id}/signaturekeys/{kid}` | DELETE | Delete signature key |

### ParticleClient (`services/particle_client.py`)
- Module-level singleton shared across all requests
- Async httpx client with auto-reconnect on token expiry
- Token refresh buffer: 5 minutes before expiry
- Supports environment switching (sandbox ↔ production) with client recreation
- Auth may return URL-encoded form data (not JSON) — parser handles both formats

## Frontend Structure

```
frontend/src/
  App.tsx              # Main app component with routing
  App.module.css       # CSS modules
  main.tsx             # Vite entry point
  api/                 # API client functions
  components/          # Reusable UI components
  pages/               # Route pages (Dashboard, Projects, ServiceAccounts, Credentials, Notifications)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PARTICLE_CLIENT_ID | (empty) | Org-level client ID (optional for auto-connect) |
| PARTICLE_CLIENT_SECRET | (empty) | Org-level client secret (optional for auto-connect) |
| PARTICLE_ENV | sandbox | Environment: sandbox or production |
| PARTICLE_TIMEOUT | 30 | HTTP timeout in seconds |

## Running

### Docker (recommended)
```bash
cd management-ui
cp .env.example .env   # Edit if needed
docker compose up --build
open http://localhost:3000
```

### Local development
```bash
# Backend
cd management-ui/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd management-ui/frontend
npm install && npm run dev   # Port 5173
```

## Security Notes

- Org credentials are sent over local Docker network only
- JWTs stored in-memory — never persisted to disk
- Client secrets passed through once, not stored
- Backend logs endpoint + status code + latency, never tokens or secrets
- No real patient data accessed — management operations only
