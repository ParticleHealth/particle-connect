# Particle E2E Integration

End-to-end integration that pulls clinical data from Particle Health into both files (CCDA) and a database (flat data → SQLite), then queries it with SQL.

## What it does

1. **Authenticates** with the Particle sandbox API
2. **Registers** a demo patient (Elvira Valadez-Nucleus)
3. **Submits a query** and polls until complete (~2-5 minutes)
4. **Retrieves CCDA data** → extracts XML documents to `ccda_documents/`
5. **Retrieves flat data** → loads into `particle_e2e.db` (SQLite)
6. **Runs SQL queries** against the database and prints results

## Prerequisites

```bash
pip install httpx
```

## Usage

```bash
# Full pipeline: API calls → CCDA files → SQLite → queries
python run_e2e.py

# Query-only mode (skip API calls, use existing database)
python run_e2e.py --queries

# Query with a specific patient ID
python run_e2e.py --queries --patient-id "abc-123"
```

## Outputs

| Output | Description |
|--------|-------------|
| `ccda_documents/` | Extracted CCDA XML files + original ZIP |
| `flat_data.json` | Raw flat data JSON from the API |
| `particle_e2e.db` | SQLite database with one table per resource type |

## SQL Queries

| Query | Description |
|-------|-------------|
| `patient_summary.sql` | Demographics + active conditions + current medications |
| `active_problems.sql` | Problem list ordered by status and onset date |
| `medication_list.sql` | Medications with dosage, route, and dates |
| `lab_results.sql` | Lab values with reference ranges and interpretation |
| `encounter_timeline.sql` | Chronological visit history with facilities |
| `data_completeness.sql` | Record counts per resource type |
| `care_team.sql` | Practitioners with specialty and organization |

All queries use SQLite dialect. Parameterized queries use `:patient_id`.

## File structure

```
particle-e2e/
├── run_e2e.py           # Main pipeline script
├── particle_client.py   # API client (auth, register, query, retrieve)
├── database.py          # SQLite schema & loading logic
├── config.py            # Sandbox credentials and paths
├── queries/
│   ├── patient_summary.sql
│   ├── active_problems.sql
│   ├── medication_list.sql
│   ├── lab_results.sql
│   ├── encounter_timeline.sql
│   ├── data_completeness.sql
│   └── care_team.sql
└── README.md
```
