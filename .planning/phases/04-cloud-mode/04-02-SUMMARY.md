---
phase: 04-cloud-mode
plan: 02
subsystem: database
tags: [bigquery, google-cloud, batch-load, idempotent, cli]

# Dependency graph
requires:
  - phase: 01-schema-foundation
    provides: "ResourceSchema dataclass and inspect_schema"
  - phase: 02-local-pipeline
    provides: "PostgreSQL loader pattern (loader.py), CLI load command, config.py"
provides:
  - "BigQuery loader module (bq_loader.py) with batch load and idempotent delete+insert"
  - "CLI --target bigquery code path"
  - "google-cloud-bigquery optional dependency"
  - "BQ_PROJECT_ID and BQ_DATASET configuration support"
affects: [04-cloud-mode, 05-api-mode]

# Tech tracking
tech-stack:
  added: ["google-cloud-bigquery>=3.40.0 (optional)"]
  patterns: ["Optional dependency with try/except ImportError fallback", "Deferred import in CLI for optional modules"]

key-files:
  created:
    - "particle-flat-observatory/src/observatory/bq_loader.py"
    - "particle-flat-observatory/tests/test_bq_loader.py"
  modified:
    - "particle-flat-observatory/src/observatory/cli.py"
    - "particle-flat-observatory/src/observatory/config.py"
    - "particle-flat-observatory/pyproject.toml"
    - "particle-flat-observatory/.env.example"

key-decisions:
  - "google-cloud-bigquery as optional dependency (not required for postgres-only users)"
  - "try/except ImportError at module top with bigquery=None fallback for testability"
  - "Wrapped CLI import of bq_loader in try/except to catch any import failure gracefully"
  - "sys.modules mock approach in tests to avoid requiring google-cloud-bigquery for test suite"

patterns-established:
  - "Optional dependency pattern: try/except import, None fallback, runtime check in entry function"
  - "CLI import error handling: wrap deferred import in try/except for graceful degradation"

# Metrics
duration: 5min
completed: 2026-02-08
---

# Phase 4 Plan 2: BigQuery Loader Summary

**BigQuery batch loader with idempotent delete+insert using load_table_from_json and parameterized DELETE, wired into CLI --target bigquery**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-08T15:23:11Z
- **Completed:** 2026-02-08T15:27:50Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created bq_loader.py mirroring loader.py structure with batch load jobs (not streaming inserts)
- Wired --target bigquery into CLI replacing stub with working code path
- Added google-cloud-bigquery as optional dependency (base install unaffected)
- Created 10 unit tests with fully mocked BigQuery client (no GCP required to test)
- All 109 tests pass (99 existing + 10 new, zero regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create BigQuery loader module and update config/deps** - `8e1108d` (feat)
2. **Task 2: Wire BigQuery target into CLI and add unit tests** - `05e09bd` (feat)

## Files Created/Modified
- `particle-flat-observatory/src/observatory/bq_loader.py` - BigQuery loader with get_bq_client, load_resource_bq, load_all_bq
- `particle-flat-observatory/tests/test_bq_loader.py` - 10 unit tests with mocked BigQuery client
- `particle-flat-observatory/src/observatory/cli.py` - Replaced bigquery stub with working code path
- `particle-flat-observatory/src/observatory/config.py` - Added bq_project_id and bq_dataset to ObservatorySettings
- `particle-flat-observatory/pyproject.toml` - Added google-cloud-bigquery optional dependency
- `particle-flat-observatory/.env.example` - Added BQ_PROJECT_ID and BQ_DATASET documentation

## Decisions Made
- **Optional dependency:** google-cloud-bigquery is in `[project.optional-dependencies]` under `bigquery = [...]` so postgres-only users are not forced to install GCP libraries. Customers install with `pip install -e ".[bigquery]"`.
- **Graceful import fallback:** bq_loader.py uses `try: from google.cloud import bigquery / except ImportError: bigquery = None` so the module can be imported (and tested) even without the package installed.
- **CLI import protection:** The deferred import `from observatory.bq_loader import ...` is wrapped in its own `try/except Exception` to catch not just ImportError but also broken dependency chains (e.g., numpy/pyarrow incompatibility).
- **sys.modules mocking in tests:** Tests inject a MagicMock into `sys.modules["google.cloud.bigquery"]` before importing bq_loader, avoiding any dependency on the actual package.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CLI import of bq_loader not wrapped in exception handler**
- **Found during:** Task 2 (CLI wiring)
- **Issue:** The deferred `from observatory.bq_loader import ...` was outside the try/except block, so if google-cloud-bigquery had broken dependencies (numpy/pyarrow incompatibility), the error would be an unhandled AttributeError instead of an actionable message.
- **Fix:** Wrapped the import itself in `try/except Exception` with an actionable error message directing users to install the package correctly.
- **Files modified:** particle-flat-observatory/src/observatory/cli.py
- **Verification:** Tested on machine with broken pyarrow; CLI now catches the error and displays instructions.
- **Committed in:** 05e09bd (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential for correct error handling. No scope creep.

## Issues Encountered
- Development machine has numpy/pyarrow incompatibility with installed google-cloud-bigquery, causing AttributeError on import. This is a local environment issue, not a code issue. The try/except ImportError in bq_loader.py and the CLI's try/except Exception both handle this gracefully.

## Next Phase Readiness
- BigQuery loader is complete and tested with mocked client
- CLI --target bigquery code path is functional
- End-to-end BigQuery testing requires: (1) valid GCP project, (2) google-cloud-bigquery properly installed, (3) authenticated gcloud
- Ready for 04-03 (Cloud Run deployment) which will use this loader in a container environment

---
*Phase: 04-cloud-mode*
*Completed: 2026-02-08*
