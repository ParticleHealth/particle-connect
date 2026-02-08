---
phase: 05-api-ingestion
plan: 02
subsystem: cli-api-integration
tags: [cli, api, normalization, typer, integration]
dependency-graph:
  requires: [05-01]
  provides: [--source api CLI path, --patient-id option, PARTICLE_* env documentation]
  affects: []
tech-stack:
  added: []
  patterns: [deferred-import-for-optional-source, unified-normalization-pipeline]
file-tracking:
  key-files:
    created:
      - particle-flat-observatory/tests/test_cli_api.py
    modified:
      - particle-flat-observatory/src/observatory/cli.py
      - particle-flat-observatory/.env.example
decisions:
  - id: 05-02-01
    decision: Deferred import of ParticleAPIClient inside if source == "api" block
    reason: Avoids importing api_client.py (and its stdlib HTTP modules) when running in file mode; follows existing cli.py pattern
  - id: 05-02-02
    decision: API response normalized via EXPECTED_RESOURCE_TYPES iteration with normalize_resource()
    reason: Guarantees identical 21-key dict shape and empty-string-to-None transformation regardless of source
  - id: 05-02-03
    decision: --patient-id silently ignored in file mode (no warning, no error)
    reason: Simplest UX -- mixed-source shell scripts work without conditional flag stripping
metrics:
  duration: 3min
  completed: 2026-02-08
  tests-before: 127
  tests-after: 132
---

# Phase 5 Plan 2: CLI API Integration Summary

**Wire ParticleAPIClient into the CLI load command, replacing the --source api stub with working API ingestion through the same downstream pipeline as file mode.**

## What Was Done

### Task 1: Wire --source api into CLI with --patient-id option
**Commit:** `c9c39c6`

Updated `cli.py` to replace the `--source api` stub ("not yet implemented") with a working integration path:

- Added `--patient-id` option with `PARTICLE_PATIENT_ID` envvar support
- When `--source api`: validates `--patient-id` is present, instantiates `ParticleAPIClient`, calls `get_flat_data(patient_id)`, normalizes response through `normalize_resource()` for each of the 21 `EXPECTED_RESOURCE_TYPES`
- When `--source file`: existing file-loading path unchanged (moved into `else` branch)
- Both source paths produce identical `dict[str, list[dict]]` shape for the downstream pipeline (schema inspection, database loading, quality report)
- Updated `.env.example` with all 7 `PARTICLE_*` environment variables (commented out, with explanatory header)

### Task 2: Add CLI integration tests for API source mode
**Commit:** `10f635b`

Created `tests/test_cli_api.py` with 5 integration tests using `typer.testing.CliRunner` and `unittest.mock`:

1. `test_api_source_missing_patient_id` -- validates `--source api` without `--patient-id` exits 1 with actionable error
2. `test_api_source_missing_credentials` -- validates missing PARTICLE_* env vars surface ValueError message
3. `test_api_source_api_request_failure` -- validates API exceptions produce "API request failed" error
4. `test_api_source_normalizes_data` -- verifies empty strings in API response become None before reaching the loader
5. `test_file_source_ignores_patient_id` -- confirms `--patient-id` is silently ignored in file mode (no regression)

## Key Links Verified

| From | To | Via | Pattern |
|------|------|------|---------|
| cli.py | api_client.py | deferred import inside `if source == "api"` | `from observatory.api_client import ParticleAPIClient` |
| cli.py | normalizer.py | `normalize_resource()` applied to API response | `normalize_resource` |
| cli.py | parser.py | `EXPECTED_RESOURCE_TYPES` used to iterate API response | `EXPECTED_RESOURCE_TYPES` |

## Deviations from Plan

None -- plan executed exactly as written.

## Test Results

132/132 tests pass (127 existing + 5 new). Zero regressions.

## Success Criteria Met

- [x] `--source api` no longer shows "not yet implemented" -- calls ParticleAPIClient
- [x] `--patient-id` is a new CLI option with PARTICLE_PATIENT_ID envvar support
- [x] API data normalized through normalize_resource() identically to file data
- [x] .env.example documents all 7 PARTICLE_* configuration variables
- [x] All existing tests pass (no regressions)
- [x] 5 new CLI integration tests pass
- [x] Both --target postgres and --target bigquery work with --source api (same downstream pipeline)

## Phase 5 Completion

With Plan 05-02 complete, Phase 5 (API Ingestion) is fully delivered. The pipeline now supports two data sources:

- **File mode** (default): `particle-pipeline load --data-path flat_data.json`
- **API mode**: `particle-pipeline load --source api --patient-id <id>`

Both paths produce identical normalized data for the downstream schema/loader/quality pipeline.
