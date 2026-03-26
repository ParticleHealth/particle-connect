# Transitions of Care (ToC) — Multi-Agent Workflow

Multi-agent orchestration system for post-discharge care coordination. Pulls patient data from Particle Health, places follow-up calls via Retell AI, sends care summary emails, with care coordinator gates at each step.

## Architecture

```
[Particle API] → Agent 1: Data → GATE 1 → Agent 2: Call → GATE 2 → Agent 3: Email → GATE 3 → Complete
                                    ↑                         ↑                          ↑
                             Coordinator reviews      Coordinator reviews        Coordinator reviews
```

**4 Agents:**
- **Data Intelligence** — Fetches flat data, builds patient context, identifies care gaps (high-risk diagnoses, missing follow-ups, medication reconciliation, abnormal labs)
- **Patient Call** — Retell AI outbound voice call with disposition tools (schedule follow-up, schedule appointment, escalate)
- **Follow-up Email** — Personalized HTML/text email via SMTP with console fallback
- **Orchestrator** — Deterministic state machine managing the 10-state pipeline

**3 Gates:** Pause points where coordinators review and approve/reject/escalate
- Gate 1: Review patient data + care gaps before placing the call
- Gate 2: Review call transcript + disposition before sending email
- Gate 3: Review email and close the case or escalate

**Signal Auto-Trigger:** Particle Signal ADT discharge events auto-create workflows

## Quick Start (Docker Compose)

The fastest way to run the full stack:

```bash
cp .env.example .env
# Edit .env with your Retell API key and phone numbers (optional for data-only mode)

docker compose up
# → Frontend: http://localhost:8080
# → Backend:  http://localhost:8000
# → API docs: http://localhost:8000/docs
```

That's it. Both services build and start together. The frontend proxies `/api` to the backend over the Docker network. SQLite data persists in `./data/`.

```bash
docker compose down       # Stop
docker compose up --build # Rebuild after code changes
```

### Local Development (without Docker)

If you prefer running directly:

```bash
# Backend
cd backend
pip install -r ../requirements.txt
cp ../.env.example ../.env
python main.py
# → http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173 (proxies /api to :8000)
```

### Docker (individual services)

You can also build and run each service separately:

```bash
# Frontend only (with backend running on host)
cd frontend
docker build -t toc-frontend .
docker run -p 8080:80 toc-frontend

# Custom backend URL
docker run -p 8080:80 -e BACKEND_URL=http://my-backend:8000 toc-frontend
```

## Demo Flow

1. Open http://localhost:5173 (dev) or http://localhost:8080 (Docker)
2. Click **Start New Workflow** — creates a workflow for the demo patient
3. Agent 1 fetches data from Particle sandbox (~2-5 min)
4. **Gate 1** appears — review patient context and care gaps, click **Approve**
5. Agent 2 places the call (requires Retell API key + phone numbers)
6. **Gate 2** appears — review transcript and disposition, click **Approve**
7. Agent 3 composes and sends the email (console output if SMTP not configured)
8. **Gate 3** appears — review email preview, click **Approve** to close

### Data-Only Mode (no Retell/SMTP needed)

The backend runs with Particle sandbox credentials out of the box. You can explore the data gathering pipeline and Gate 1 without configuring Retell or SMTP.

## Project Structure

```
care-coordination-toc/
├── docker-compose.yml           # Full stack: backend + frontend
├── requirements.txt             # Python: httpx, fastapi, uvicorn, pydantic
├── .env.example                 # Environment variable template
├── .gitignore
│
├── backend/
│   ├── Dockerfile               # Python 3.12-slim + uvicorn
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Environment-based configuration
│   ├── database.py              # SQLite schema + CRUD (6 tables)
│   ├── models.py                # Pydantic models + enums
│   ├── agents/
│   │   ├── base.py              # Base agent contract
│   │   ├── data_intelligence.py # Agent 1: Particle data → patient context
│   │   ├── patient_call.py      # Agent 2: Retell AI outbound call
│   │   ├── followup_email.py    # Agent 3: Email composition + sending
│   │   └── orchestrator.py      # State machine + pipeline management
│   ├── services/
│   │   ├── particle_client.py   # Async Particle API client
│   │   ├── call_context.py      # Flat data → structured context + care gaps
│   │   ├── prompt_builder.py    # Voice agent prompt template
│   │   ├── voice_client.py      # Async Retell AI client
│   │   ├── email_client.py      # SMTP + console fallback email sender
│   │   └── signal_listener.py   # Particle Signal webhook parsing
│   ├── routers/
│   │   ├── workflows.py         # Workflow CRUD + start/cancel/retry
│   │   ├── gates.py             # Gate decision endpoints
│   │   ├── patients.py          # Patient listing
│   │   ├── webhooks.py          # Retell call event receiver
│   │   └── signal.py            # Signal ADT auto-trigger
│   └── tests/                   # pytest: 19 tests (database + orchestrator)
│
├── frontend/
│   ├── Dockerfile               # Multi-stage: node:22 build → nginx:alpine serve
│   ├── nginx.conf.template      # Nginx config with envsubst for BACKEND_URL
│   └── src/
│       ├── App.tsx              # Root: sidebar + page routing
│       ├── api/client.ts        # Typed API client
│       ├── components/          # Sidebar, WorkflowTimeline, GateControl,
│       │                        # PatientSummaryCard, StatusBadge, EmailPreview
│       └── pages/               # DashboardPage, WorkflowDetailPage
│
└── e2e_test.py                  # Playwright + Chromium E2E test (8 steps)
```

## State Machine

```
PENDING → DATA_GATHERING → GATE_1_PENDING → CALLING → GATE_2_PENDING → EMAILING → GATE_3_PENDING → COMPLETED
              ↓                  ↓              ↓            ↓              ↓              ↓
           FAILED          CANCELLED          FAILED     COMPLETED*      FAILED        COMPLETED
                                                        (no email)
```

Terminal states: COMPLETED, FAILED (retryable), CANCELLED

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health check |
| GET | `/api/workflows` | List workflows (filter by `?status=`) |
| POST | `/api/workflows` | Create workflow for a patient |
| GET | `/api/workflows/{id}` | Full workflow detail (context + call + email + gates + events) |
| POST | `/api/workflows/{id}/start` | Trigger Agent 1 (data gathering) |
| POST | `/api/workflows/{id}/cancel` | Cancel an active workflow |
| POST | `/api/workflows/{id}/retry` | Retry a failed step |
| GET | `/api/workflows/{id}/events` | Audit trail event log |
| GET | `/api/workflows/{id}/gates` | List all gate statuses |
| GET | `/api/workflows/{id}/gates/{n}` | Gate detail with review data |
| POST | `/api/workflows/{id}/gates/{n}/decide` | Submit gate decision (approve/reject/escalate) |
| GET | `/api/patients` | List demo patients |
| POST | `/api/webhooks/call-events` | Retell call completion webhook |
| POST | `/api/webhooks/signal` | Particle Signal ADT event → auto-create workflow |
| POST | `/api/signal/subscribe/{patient_id}` | Subscribe patient to Signal monitoring |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PARTICLE_CLIENT_ID` | Sandbox ID | Particle API client ID |
| `PARTICLE_CLIENT_SECRET` | Sandbox secret | Particle API client secret |
| `RETELL_API_KEY` | _(empty)_ | Retell AI API key (required for calls) |
| `RETELL_FROM_NUMBER` | _(empty)_ | Retell outbound caller ID |
| `DEMO_OVERRIDE_PHONE` | _(empty)_ | Your phone number for testing |
| `WEBHOOK_URL` | `http://localhost:8000/api/webhooks/call-events` | Retell webhook URL |
| `SMTP_HOST` | _(empty)_ | SMTP server (empty = console fallback) |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | _(empty)_ | SMTP username |
| `SMTP_PASSWORD` | _(empty)_ | SMTP password |
| `EMAIL_FROM` | `care-team@example.com` | Sender email address |
| `SIGNAL_WEBHOOK_SECRET` | _(empty)_ | HMAC secret for Signal webhook verification |
| `DB_PATH` | `toc_workflow.db` | SQLite database path |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins |

## Testing

```bash
# Unit tests (database + orchestrator state machine)
cd backend && python3 -m pytest tests/ -v

# E2E test with Playwright + Chromium (starts servers, walks through full workflow)
cd care-coordination-toc && python3 e2e_test.py
# → Saves 8 screenshots to screenshots/
```

## Dependencies

**Backend:** httpx, fastapi, uvicorn, pydantic (+ stdlib: sqlite3, smtplib, email)
**Frontend:** react 19, react-dom, vite 6, typescript
**Docker:** node:22-alpine (build), nginx:alpine (serve)
**E2E tests:** playwright (with Chromium)
