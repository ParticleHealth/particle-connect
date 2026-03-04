# Particle Health Management API — Admin UI

A dockerized admin interface for the [Particle Health Management API](https://docs.particlehealth.com/docs/management-apis). Lets you create projects, manage service accounts, and rotate credentials — all from a browser.

## What You Can Do

| Feature | Description |
|---------|-------------|
| **Authenticate** | Connect with your org-level Client ID and Secret |
| **Projects** | List, create, activate/deactivate Covered Entity projects |
| **Service Accounts** | Create accounts, assign IAM roles to projects |
| **Credentials** | Generate, rotate, and revoke Client ID/Secret pairs |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Particle Health organization credentials (Client ID + Client Secret from your Particle representative)

## Quick Start

```bash
# 1. Clone and navigate
cd demos/management-ui

# 2. Copy env file and set your base URL (credentials entered in the UI)
cp .env.example .env
# Edit .env if you need to change PARTICLE_BASE_URL (default: sandbox)

# 3. Start
docker compose up --build

# 4. Open
open http://localhost:3000
```

Enter your org-level Client ID and Client Secret in the login screen to connect.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  React Frontend │────▶│  FastAPI Backend  │────▶│  Particle Health     │
│  (nginx :3000)  │     │  (proxy :8000)    │     │  Management API      │
└─────────────────┘     └──────────────────┘     └──────────────────────┘
```

- **Frontend** — React 19 + TypeScript, served by nginx. Proxies `/api` requests to the backend.
- **Backend** — FastAPI app that authenticates with Particle, caches the JWT in-memory, and proxies management operations.
- **No database** — all state comes from Particle's API. JWT is held in memory only.

## Pages

### Login
Enter org credentials. The backend calls Particle's `/auth` endpoint and caches the JWT.

### Dashboard
Overview with project and service account counts. Quick-action buttons to create new resources.

### Projects
Table of all projects with name, NPI, status, and location. Create new projects with the form. Toggle active/inactive state.

### Service Accounts
Table of all service accounts. Create new accounts, assign IAM policies (role + project bindings).

### Credentials
Per-service-account credential management. Create/rotate credentials with configurable old-credential TTL. **Client secrets are shown only once** — copy them immediately.

## Security Notes

- Org credentials are sent to the backend over the local Docker network only
- JWTs are stored in-memory on the backend — never persisted to disk
- Client secrets from credential creation are passed through once and not stored
- No real patient data is accessed — this is management/admin operations only
- The backend logs endpoint, status code, and latency — never tokens or secrets

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `PARTICLE_BASE_URL` | `https://sandbox.particlehealth.com` | Particle API base URL |
| `PARTICLE_TIMEOUT` | `30` | HTTP timeout in seconds for Particle API calls |

## Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # runs on :5173
```

## Roles Reference

| Role | Management API | Query Flow API |
|------|---------------|----------------|
| `organization.owner` | Full access | No |
| `project.owner` | Project-scoped | Yes |
| `project.user` | No | Yes |
