# Doc Reviewer Agent Memory

## Last Updated
2026-03-06 — First full review completed.

## Repo Snapshot
- **Doc files**: 10 numbered files (01-10), README.md, AGENTS.md, llms.txt in `agent-documentation/`
- **Sub-projects**: particle-api-quickstarts (Python SDK with 4 modules: patient, query, document, signal), particle-analytics-quickstarts (DuckDB/BQ pipeline), management-ui (React + FastAPI)
- **Source paths**: `particle-api-quickstarts/src/particle/`, `particle-analytics-quickstarts/src/observatory/`, `management-ui/backend/app/`, `management-ui/frontend/src/`
- **SDK modules**: core, patient, query, document, signal
- **Analytics modules**: cli, config, api_client, parser, schema, normalizer, loader, bq_loader, ddl, quality, generate_ddl
- **Management UI routers**: auth, projects, service_accounts, credentials, notifications

## Known Drift Issues
None remaining after 2026-03-06 review.

## Fixed Issues (2026-03-06)
- **CRITICAL**: llms.txt had WRONG address_state instruction — said "never use abbreviations" when API requires abbreviations. Fixed.
- Signal module (src/particle/signal/) was completely undocumented — added to 01, 02, 04, 07, 09, 10, llms.txt, AGENTS.md
- Signal workflows (4 scripts) and quick-starts (3 scripts) were missing from 04-sdk-reference.md
- Notifications router endpoints were skeletal in 03-management-api-reference.md — added request/response bodies
- Notifications page missing from 06-management-ui.md frontend page list and endpoint table
- Notification + SignatureKey models missing from 07-data-models.md
- Analytics `--source api` mode and `observatory-generate-ddl` CLI undocumented in 05
- Signal-specific env vars (SIGNAL_CALLBACK_URL, WEBHOOK_PORT) missing from 10-environment-setup.md
- Signal-specific troubleshooting entries missing from 09
- Usage example in 04-sdk-reference.md used "New York" instead of "NY" for address_state

## Improvement Backlog
- Consider splitting 02-api-reference.md now that Signal endpoints added (approaching 250+ lines)
- 07-data-models.md is growing — may need to split Signal models into separate file if more models added
- Management API notification types (query, patient, networkalert, hl7v2) could use descriptions of what triggers each type
- No test coverage documented for Signal module (tests/test_signal.py may not exist yet)

## Review History
- 2026-03-06: Full review — all 13 doc files reviewed, 11 files updated, 1 critical error fixed (llms.txt address_state)
