# Environment Setup

Prerequisites and configuration for all three sub-projects.

## Global Prerequisites

- Python 3.11+
- Git

## particle-api-quickstarts Setup

### Install
```bash
cd particle-api-quickstarts
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configure Credentials
```bash
cp .env.example .env
```

Edit `.env`:
```
PARTICLE_CLIENT_ID=your-client-id
PARTICLE_CLIENT_SECRET=your-client-secret
PARTICLE_SCOPE_ID=projects/your-scope-id
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PARTICLE_CLIENT_ID | Yes | — | Project-level client ID |
| PARTICLE_CLIENT_SECRET | Yes | — | Project-level client secret |
| PARTICLE_SCOPE_ID | Yes | — | Scope ID (format: `projects/<id>`) |
| PARTICLE_BASE_URL | No | `https://sandbox.particlehealth.com` | API base URL |
| PARTICLE_TIMEOUT | No | 30 | Request timeout in seconds |

### Verify
```bash
python workflows/check_setup.py
```

Expected output:
```
Checking Particle Health API setup...
1. Checking environment variables... OK
2. Testing authentication... OK
--- Setup OK ---
Environment: sandbox
```

### Run Demo
```bash
python workflows/hello_particle.py
```

## particle-analytics-quickstarts Setup

### Install (Local DuckDB)
```bash
cd particle-analytics-quickstarts
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Install (BigQuery)
```bash
pip install -e ".[bigquery]"
gcloud auth application-default login
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| FLAT_DATA_PATH | No | `sample-data/flat_data.json` | Input data path |
| DUCKDB_PATH | No | `observatory.duckdb` | DuckDB file path |
| LOG_LEVEL | No | INFO | Logging level |
| BQ_PROJECT_ID | For BigQuery | — | GCP project ID |
| BQ_DATASET | No | `particle_observatory` | BigQuery dataset |

### Verify (DuckDB)
```bash
particle-pipeline
```

### BigQuery Infrastructure
```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars   # Set project_id
terraform init && terraform apply
```

## management-ui Setup

### Docker (recommended)
```bash
cd management-ui
cp .env.example .env    # Set credentials for auto-connect (optional)
docker compose up --build
open http://localhost:3000
```

### Local Development
```bash
# Backend
cd management-ui/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd management-ui/frontend
npm install
npm run dev
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PARTICLE_CLIENT_ID | No | (empty) | Org-level client ID for auto-connect |
| PARTICLE_CLIENT_SECRET | No | (empty) | Org-level client secret for auto-connect |
| PARTICLE_ENV | No | sandbox | Environment: sandbox or production |
| PARTICLE_TIMEOUT | No | 30 | HTTP timeout in seconds |

If credentials are set in .env, the backend auto-connects on startup. Otherwise, connect via the UI login page.

## Switching to Production

### Query Flow API
```bash
export PARTICLE_BASE_URL="https://api.particlehealth.com"
```

### Management UI
Use the environment switch in the UI, or set in .env:
```
PARTICLE_ENV=production
```

### Key Differences in Production
- FHIR format becomes available
- Auth URL changes to `api.particlehealth.com`
- Management URL changes to `management.particlehealth.com`
- Real patient data — handle with appropriate care and compliance
