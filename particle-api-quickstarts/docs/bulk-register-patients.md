# Bulk Patient Registration

`workflows/bulk_register_patients.py` registers many patients from a CSV file using the same
SDK calls as `workflows/register_patient.py` (`POST /api/v2/patients`). It adds only what a
bulk load needs: CSV parsing, pacing, resume, and result/reject files.

It is **safe by default**: without `--execute` it only validates the CSV and makes no API calls.

## Prerequisites

1. **Credentials** (only needed with `--execute`; validate-only runs make no API calls and need none).
   You need a `client_id`, `client_secret` and project scope from the
   **Particle Account Team**. Ask them to provision a service account and credential for the
   project you are loading into, and to confirm the base URL (sandbox or production) and the
   request rate they recommend for your account.
2. **Environment.** Python 3.14+ and the SDK installed (see the main [README](../README.md)).
3. **`.env`** in `particle-api-quickstarts/` (never commit this file):

   ```
   PARTICLE_CLIENT_ID=<from the Account Team>
   PARTICLE_CLIENT_SECRET=<from the Account Team>
   PARTICLE_SCOPE_ID=projects/<project-id>      # note the "projects/" prefix
   PARTICLE_BASE_URL=https://api.particlehealth.com   # or your sandbox URL
   ```

## CSV format

Start from the template: [`sample-data/bulk_patients_template.csv`](../sample-data/bulk_patients_template.csv)
(all values are placeholders; replace them with your own).

One patient per row. Column names are case-sensitive; a parenthesized hint after a name
(e.g. `gender(MALE/FEMALE)`) and a leading "Body Params" line (as exported by Postman) are
both accepted.

**Required** (the API rejects a patient without these):

| Column | Notes |
|---|---|
| `patient_id` | Your unique external ID for the patient (unique within a project; the API lower-cases it) |
| `given_name`, `family_name` | Surrounding whitespace is trimmed |
| `date_of_birth` | `YYYY-MM-DD` |
| `gender` | `MALE` or `FEMALE` |
| `address_city`, `address_state`, `postal_code` | ZIP is `12345` or `12345-6789`; the state may be a 2-letter code or a full name (the API converts names to codes) |

**Optional:**

| Column | Notes |
|---|---|
| `project_id` | Target project for this row (see [Multiple projects](#multiple-projects)). Blank uses `PARTICLE_SCOPE_ID` |
| `address_lines` | Street address |
| `telephone` | Any common US format; normalized to `XXX-XXX-XXXX` |
| `ssn` | `XXX-XX-XXXX` |
| `email` | |

```csv
project_id,patient_id,given_name,family_name,date_of_birth,gender,address_lines,address_city,address_state,postal_code,telephone,ssn,email
,EXAMPLE-0001,Sample,Patientone,1970-01-01,FEMALE,123 Example Street,Anytown,NY,12345,555-555-0101,,
```

## Multiple projects

An organization can have more than one project. Patients belong to one project, and the project
is chosen when the access token is requested (the `scope` of `GET /auth`), not on each API
call. So:

- **One project (default):** set `PARTICLE_SCOPE_ID=projects/<project-id>` and leave `project_id`
  blank or omit the column.
- **Several projects in one file:** add a `project_id` column (a bare ID or `projects/<id>`).
  The script keeps one token per project. The credential must have access to **every** project
  you list; ask the Account Team to grant a service account access to the additional projects,
  or run once per project with separate credentials.
- An organization-level scope cannot register patients; use project IDs.
- The same `patient_id` may appear in different projects. Resume treats `(project, patient_id)`
  as the key.

## Usage

Run from `particle-api-quickstarts/`:

```bash
# 1. Validate only: parses every row, writes bad rows to the rejects file, calls no API
python workflows/bulk_register_patients.py patients.csv

# 2. Small trial against the API
python workflows/bulk_register_patients.py patients.csv --execute --limit 5 --per-minute 10

# 3. Full run
python workflows/bulk_register_patients.py patients.csv --execute --per-minute 60
```

| Option | Default | Meaning |
|---|---|---|
| `--execute` | off | Actually call the API (otherwise validate only) |
| `--per-minute N` | 60 | Maximum registrations per minute **across all workers** |
| `--workers N` | 2 | Concurrent registrations (see [Speed](#speed)) |
| `--no-verify` | off | Skip the read-back check described below (saves one GET per patient) |
| `--limit N` | none | Register at most N patients this run, N >= 0 (applied after validation and resume) |
| `--results PATH` | `bulk_results.csv` | Successes: `patient_id, scope, base_url, particle_patient_id, registered_at` |
| `--rejects PATH` | `bulk_rejects.csv` | Failures: `row, patient_id, scope, stage, error` (`stage` is `validate`, `api` or `verify`) |

Example output:

```
CSV rows=2000 already_done=0 invalid=1 to_register_this_run=1999
Registering against https://api.particlehealth.com scope=projects/... at 60/min
[w1] 1/1999 patient_id=ext-001 PPID=3f1c9a2e... create=850ms get=420ms (verified)
[w2] FAILED 2/1999 patient_id=ext-002: 400: <message>
INVALID row 17 patient_id=ext-017: postal_code: String should match pattern ...
```

## Speed

Each registration is a synchronous API call that can take a second or more, so a single worker
is limited to about `1 / latency` patients per second. `--workers N` runs N registrations
concurrently (default 2). `--per-minute` is still a hard cap on the combined rate, so raise both
together; for example `--workers 4 --per-minute 240`.

- Start with the default, watch for `rate limited` messages and `FAILED` lines, then step up.
  Confirm a safe rate with the Particle Account Team before a large load.
- A `THROUGHPUT last 60s: N registered (done/total, failed, minutes elapsed)` line prints every
  minute. If N is below `--per-minute`, the workers are the limit, so add workers; if N is at
  `--per-minute`, raise that too.
- A `429` makes **every** worker pause for the `Retry-After` period, not just the one that
  received it.
- Output lines appear in completion order, so `7/2000` may print before `6/2000`.
  `[wN]` is the worker, `create`/`get` are API latencies in ms. Each worker keeps its own token.
- A fatal condition (bad credentials, or 10 consecutive failures) stops all workers; requests
  already in flight finish. Ctrl-C does the same.

## Behavior

- **Read-back verification.** After each successful registration the script reads the patient back
  (`GET /api/v2/patients/{particle_patient_id}`) and checks that the stored `particle_patient_id`,
  `patient_id`, names, date of birth, gender, city, state and ZIP match what the API accepted
  (so server-side normalization, such as state codes, is not flagged). Only verified patients are
  written to the results file. A patient that registers but fails the check is recorded in the
  rejects file with `stage=verify`, the Particle patient ID and the mismatched field names (never
  values); rerunning re-submits it (safe: same demographics are an update) and checks again.
  This adds one GET per patient; `--no-verify` turns it off.
- **Resume.** Rerun the same command. A patient already in the results file **for the same API
  URL and project** is skipped, so an interrupted run (Ctrl-C, network loss) continues where it
  stopped, and a sandbox trial never causes production rows to be skipped. Rows that failed are
  retried on the next run. A results/rejects file written by an older version of the script has
  different columns; the script refuses to append to it, so move it aside.
- **Idempotent registration.** The API treats the same `patient_id` with the same demographics as
  an update, and the same `patient_id` with different demographics as an error.
- **Rate limits.** On HTTP 429 the script waits for `Retry-After` (30s if absent) and retries up
  to 5 times before recording the row as failed.
- **Fail fast.** The run (all workers) stops on an authentication failure (exit 2, naming the project) or
  after 10 consecutive API failures (exit 3), rather than writing thousands of rejects during an
  outage. Ctrl-C exits 130. Exit 1 means the run finished but some rows were invalid or failed.
- **Spreadsheet safe.** IDs that start with `=`, `+`, `-` or `@` are written with a leading `'`
  so a spreadsheet does not run them as formulas; the script reverses this when it resumes.
- **No demographics in logs or files.** The `--results` and `--rejects` files contain only the
  fields listed in the option table above (your `patient_id`, the Particle patient ID, the
  project scope, API URL, timestamp, row number, stage and an error summary). The console output
  adds worker IDs, progress counters and latencies, and no demographic values appear in it
  either. The files are still linked to your patients, so store them accordingly.

## Before a large load

Registering a patient can trigger downstream behavior depending on how your account is
configured. Before loading a large file, confirm with the Particle Account Team:

- the request rate you should use,
- what happens automatically when a patient is registered for your account, and
- that you have tried a small `--limit` run first.
