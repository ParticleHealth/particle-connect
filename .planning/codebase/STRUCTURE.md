# Codebase Structure

**Analysis Date:** 2026-02-07

## Directory Layout

```
particle-connect/
├── particle-health-starters/          # Main deliverable - Python SDK and examples
│   ├── src/particle/                  # Installable Python package
│   │   ├── core/                      # Infrastructure (config, auth, HTTP, logging)
│   │   ├── query/                     # Query submission, polling, data retrieval
│   │   ├── patient/                   # Patient registration and management
│   │   └── document/                  # Document submission
│   ├── workflows/                     # Production-like reference implementations
│   ├── quick-starts/python/           # Minimal quick-start examples (no services)
│   ├── tests/                         # Integration tests for core infrastructure
│   ├── sample-data/                   # Sample JSON data for testing/demos
│   ├── pyproject.toml                 # Package metadata and dependencies
│   └── .planning/config.json          # Planning configuration
├── .planning/codebase/                # Codebase analysis documents (this directory)
├── CLAUDE.local.md                    # Project-specific instructions
├── README.md                          # Repository overview
├── LICENSE                            # Apache 2.0
└── .gitignore                         # Git exclusions
```

## Directory Purposes

**`src/particle/`:**
- Purpose: Python package providing Particle Health API client and services
- Contains: Service classes, models, and infrastructure
- Key files: `__init__.py` (exports), core infrastructure, domain modules

**`src/particle/core/`:**
- Purpose: Shared infrastructure used by all services
- Contains: Configuration, authentication, HTTP client, exceptions, logging
- Key files: `config.py`, `auth.py`, `http.py`, `exceptions.py`, `logging.py`, `__init__.py`

**`src/particle/query/`:**
- Purpose: Clinical data query operations
- Contains: `QueryService` (submit, poll, retrieve), `QueryStatus`/`PurposeOfUse` enums, `QueryRequest`/`QueryResponse` models
- Key files: `service.py`, `models.py`, `__init__.py`

**`src/particle/patient/`:**
- Purpose: Patient registration and demographic management
- Contains: `PatientService` (register), `PatientRegistration` model, `Gender` enum
- Key files: `service.py`, `models.py`, `__init__.py`

**`src/particle/document/`:**
- Purpose: Document submission for patients
- Contains: `DocumentService` (submit), `DocumentSubmission`/`DocumentResponse` models, `DocumentType`/`MimeType` enums
- Key files: `service.py`, `models.py`, `__init__.py`

**`workflows/`:**
- Purpose: Production-like reference implementations demonstrating best practices
- Contains: Complete CLI scripts showing error handling, structured logging, service usage
- Key files: `register_patient.py`, `submit_query.py`, `submit_document.py`, `retrieve_data.py`

**`quick-starts/python/`:**
- Purpose: Minimal quick-start examples for fast validation
- Contains: Simple scripts using only httpx + stdlib (no service layer)
- Key files: `auth.py`, `register_patient.py`, `submit_query.py`, `retrieve_data.py`

**`tests/`:**
- Purpose: Integration tests for core infrastructure components
- Contains: Tests for config loading, auth token management, exception hierarchy, logging/redaction
- Key files: `test_core_integration.py`, `__init__.py`

**`sample-data/`:**
- Purpose: Sample data files for testing and demonstrations
- Contains: JSON test fixtures
- Key files: `flat_data.json` (sample flat format response)

## Key File Locations

**Entry Points:**
- `src/particle/__init__.py`: Package entry point; exports services and models
- `workflows/register_patient.py`: Production-like patient registration example
- `workflows/submit_query.py`: Production-like query submission example
- `quick-starts/python/submit_query.py`: Minimal query submission example
- `quick-starts/python/register_patient.py`: Minimal registration example

**Configuration:**
- `src/particle/core/config.py`: `ParticleSettings` loads from PARTICLE_* environment variables
- `pyproject.toml`: Package metadata, dependencies, build config

**Core Logic:**
- `src/particle/core/auth.py`: `ParticleAuth` + `TokenManager` for JWT token lifecycle
- `src/particle/core/http.py`: `ParticleHTTPClient` with retry logic and error mapping
- `src/particle/query/service.py`: `QueryService` - query submission, polling, data retrieval
- `src/particle/patient/service.py`: `PatientService` - patient registration
- `src/particle/document/service.py`: `DocumentService` - document submission

**Models:**
- `src/particle/query/models.py`: QueryRequest, QueryResponse, QueryStatus, PurposeOfUse
- `src/particle/patient/models.py`: PatientRegistration, PatientResponse, Gender
- `src/particle/document/models.py`: DocumentSubmission, DocumentResponse, DocumentType, MimeType

**Testing:**
- `tests/test_core_integration.py`: Tests for ParticleSettings, exceptions, auth, logging, HTTP client

**Exceptions:**
- `src/particle/core/exceptions.py`: ParticleError base class + 8 specific subclasses

**Logging:**
- `src/particle/core/logging.py`: configure_logging(), redact_phi processor, PHI pattern definitions

## Naming Conventions

**Files:**
- Modules named by function: `config.py`, `auth.py`, `http.py`, `logging.py`, `exceptions.py`, `models.py`, `service.py`
- Test files: `test_*.py` (e.g., `test_core_integration.py`)
- Workflow scripts: `{operation}_{noun}.py` (e.g., `submit_query.py`, `register_patient.py`)

**Directories:**
- Domain modules (plural): `query/`, `patient/`, `document/`
- Infrastructure module: `core/`
- Runnable examples: `workflows/`, `quick-starts/`
- Test directory: `tests/`

**Classes:**
- Service classes: `{Domain}Service` (e.g., `QueryService`, `PatientService`)
- Model classes: `{Entity}{Type}` (e.g., `QueryResponse`, `PatientRegistration`)
- Enum classes: Uppercase with underscores or CamelCase (e.g., `QueryStatus`, `PurposeOfUse`)

**Functions:**
- Public methods: `snake_case` (e.g., `submit_query()`, `wait_for_query_complete()`)
- Private methods: `_snake_case` prefix (e.g., `_handle_response()`, `_build_token_request()`)
- Processors: Lowercase with underscores (e.g., `redact_phi()`, `configure_logging()`)

**Constants:**
- Config keys: `PARTICLE_*` for environment variables (e.g., `PARTICLE_CLIENT_ID`)
- Error codes: lowercase with underscores (e.g., `"auth_error"`, `"query_timeout"`)
- Timeout values: descriptive names with suffix `_seconds` (e.g., `timeout_seconds`, `token_refresh_buffer_seconds`)

## Where to Add New Code

**New Feature (e.g., new API operation):**
- Primary code: `src/particle/{domain}/service.py` (add method to service class)
- Data models: `src/particle/{domain}/models.py` (add request/response Pydantic models)
- Tests: `tests/test_{domain}.py` (new file if domain not tested yet)
- Example: `workflows/{operation}_{noun}.py` (new workflow script)
- Quick-start: `quick-starts/python/{operation}_{noun}.py` (minimal example)

**New Domain Module (e.g., handling a new API resource):**
- Create `src/particle/{domain_name}/` directory
- Create `src/particle/{domain_name}/__init__.py` with exports
- Create `src/particle/{domain_name}/models.py` with Pydantic models and enums
- Create `src/particle/{domain_name}/service.py` with service class
- Update `src/particle/__init__.py` to export new service

**Utilities and Helpers:**
- Shared across domains: `src/particle/core/` (e.g., new logging processor, auth handler)
- Domain-specific helpers: Keep in `src/particle/{domain}/service.py` or break into separate file if complex

**Tests:**
- Core infrastructure tests: `tests/test_core_integration.py` (extend existing)
- Domain tests: `tests/test_{domain}.py` (create new file for new domain)
- Fixtures: Use pytest fixtures in same file; move to `conftest.py` if reused

## Special Directories

**`src/particle/` (Package Root):**
- Purpose: Package entry point and public API
- Generated: No
- Committed: Yes
- Contents: `__init__.py` with all public exports

**`.planning/`:**
- Purpose: Stores planning and codebase analysis documents
- Generated: No
- Committed: Yes
- Contents: `codebase/` subdirectory with ARCHITECTURE.md, STRUCTURE.md, etc.

**`.venv/`:**
- Purpose: Python virtual environment for development
- Generated: Yes (by `python -m venv .venv`)
- Committed: No (in .gitignore)

**`.pytest_cache/`:**
- Purpose: pytest cache for test discovery and execution
- Generated: Yes (by pytest runner)
- Committed: No (in .gitignore)

**`sample-data/`:**
- Purpose: Sample API responses and test fixtures
- Generated: No
- Committed: Yes
- Contents: JSON files for testing and examples

---

*Structure analysis: 2026-02-07*
