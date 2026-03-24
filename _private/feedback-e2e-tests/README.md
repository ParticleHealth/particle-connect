# Agent Feedback E2E Tests

These three one-shot prompts test whether a coding agent, after reading the Particle Connect agent documentation, **voluntarily submits feedback** via the protocol in `14-agent-feedback.md`.

## How to Run

Give each prompt to a coding agent (Claude Code, Cursor, Devin, etc.) in a fresh session with this repo as the working directory. Do NOT mention feedback — the agent must discover it from `llms.txt`.

## What to Check

After each test, check the Google Sheet linked to the Particle Agent Feedback Form for a new row. Record:

| Test | Agent | Submitted Feedback? | Outcome Reported | Errors Reported | Docs Listed |
|------|-------|---------------------|------------------|-----------------|-------------|
| 1    |       |                     |                  |                 |             |
| 2    |       |                     |                  |                 |             |
| 3    |       |                     |                  |                 |             |

## Prompts

### Happy Path (should succeed)
- `prompt-1-flat-data-e2e.md` — Retrieve flat data and query it with DuckDB
- `prompt-2-signal-webhook.md` — Signal/ADT webhook setup
- `prompt-3-bidirectional-submit.md` — Document submission round-trip

### Error Traps (designed to surface mistakes)
- `prompt-4-fhir-trap.md` — Asks for FHIR R4 data, which returns 404 in sandbox
- `prompt-5-oauth2-trap.md` — Asks for OAuth2 auth + uses full state name "Massachusetts" — both wrong
- `prompt-6-wrong-api-mix.md` — Mixes Management API + Query Flow API in one script — different base URLs and auth flows
