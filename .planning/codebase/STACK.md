# Technology Stack

**Analysis Date:** 2026-02-07

## Languages

**Primary:**
- Python 3.11+ - Core SDK and all scripts
- Shell (Bash) - Quick-start curl examples and utility scripts

**Secondary:**
- YAML - Configuration and workflow files

## Runtime

**Environment:**
- Python 3.11 or higher (specified in `pyproject.toml`: `requires-python = ">=3.11"`)

**Package Manager:**
- uv - Modern Python package manager (referenced in quick-starts)
- pip - Standard Python package installer (fallback for standard environment setup)
- Lockfile: `uv.lock` present at `/Users/sangyetsakorshika/Documents/GitHub/particle-connect/particle-health-starters/uv.lock`

## Frameworks

**Core:**
- Pydantic 2.0+ - Data validation, settings management, and schema modeling
- Pydantic-settings 2.0+ - Environment variable configuration management
- httpx 0.28+ - Async-capable HTTP client (used in sync mode with context managers)
- structlog 25.0+ - Structured logging with PHI redaction support
- tenacity 9.0+ - Retry logic with exponential backoff and jitter
- PyJWT 2.0+ - JWT token decoding and validation

**Testing:**
- pytest 8.0+ - Test runner
- pytest-asyncio 0.24+ - Async test support

**Build/Dev:**
- Hatchling - Python package build backend
- ruff 0.1+ - Python linter and formatter (type: py311, line-length: 100)

## Key Dependencies

**Critical:**
- `httpx` - HTTP client with automatic timeout, retry configuration, and auth integration
  - Location: `src/particle/core/http.py`
  - Why: Handles all Particle API communication with custom auth flow
- `pydantic` - Request/response validation
  - Location: Throughout `src/particle/` modules
  - Why: Ensures type safety and validates API responses before use
- `structlog` - Structured logging with automatic PHI/PII redaction
  - Location: `src/particle/core/logging.py`
  - Why: HIPAA compliance - prevents sensitive patient data in logs

**Infrastructure:**
- `tenacity` - Automatic retry with exponential backoff
  - Location: `src/particle/core/http.py` decorator on `_request_with_retry()`
  - Why: Handles transient network failures (timeouts, connection errors)
- `PyJWT` - JWT token parsing and expiry detection
  - Location: `src/particle/core/auth.py`
  - Why: Extracts token expiry from JWT to enable proactive refresh

## Configuration

**Environment:**
- Configuration via environment variables with `PARTICLE_` prefix:
  - `PARTICLE_CLIENT_ID` (required) - API client identifier
  - `PARTICLE_CLIENT_SECRET` (required) - API credential (marked as SecretStr to prevent logging)
  - `PARTICLE_SCOPE_ID` (required) - Project/scope identifier
  - `PARTICLE_BASE_URL` (optional, defaults to `https://sandbox.particlehealth.com`)
  - `PARTICLE_TIMEOUT` (optional, defaults to 30.0 seconds)
  - Token refresh buffer: 600 seconds (10 minutes before 1-hour token expiry)

  **Location:** `src/particle/core/config.py` - `ParticleSettings` class

- `.env` file support: pydantic-settings automatically loads from `.env` in working directory

**Build:**
- `pyproject.toml` at `/Users/sangyetsakorshika/Documents/GitHub/particle-connect/particle-health-starters/pyproject.toml`:
  - Package name: `particle-starter`
  - Wheel packages: `src/particle`
  - Ruff configuration: line-length=100, target-version=py311, lint rules E, F, I, W
  - pytest configuration: testpaths=["tests"], pythonpath=["src"]

## Platform Requirements

**Development:**
- Python 3.11+
- Virtual environment (`.venv` directory)
- Bash shell (for quick-start curl scripts)
- Standard Unix tools (curl for HTTP examples)

**Production:**
- Python 3.11+ runtime
- Network access to Particle Health API endpoints:
  - Sandbox: `https://sandbox.particlehealth.com`
  - Production: `https://api.particlehealth.com`
- 30-second request timeout (configurable via `PARTICLE_TIMEOUT`)

## Optional Dependencies

**Development (dev extras):**
- pytest>=8.0.0 - Test execution
- pytest-asyncio>=0.24.0 - Async test support
- ruff>=0.1.0 - Linting and formatting

Install with: `pip install -e ".[dev]"`

---

*Stack analysis: 2026-02-07*
