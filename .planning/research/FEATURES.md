# Feature Research

**Domain:** Healthcare data pipeline accelerator / starter kit (Particle Health Flat API to PostgreSQL/BigQuery)
**Researched:** 2026-02-07
**Confidence:** HIGH (features derived from actual Particle Health Flat API data structure, verified healthcare data pipeline patterns, and established data engineering best practices)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = accelerator feels broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **DDL generation for all 21 resource types** | The whole point of the accelerator; customers need tables for every Flat API resource type (patients, encounters, labs, medications, problems, vitalSigns, procedures, etc.) | MEDIUM | Must handle all 21 top-level keys from the Flat response. Auto-generate from sample data or schema definition. Include column types, nullable constraints. |
| **Dual ingestion mode (API live + file load)** | Customers need to demo from file (no API credentials needed) and run live in production; file mode is critical for "works from clean checkout" promise | MEDIUM | File mode loads from `flat_data.json`. API mode calls Particle Health GET Flat endpoint. Same downstream pipeline regardless of source. |
| **Docker PostgreSQL local mode** | Data engineers expect `docker compose up` and done; local mode must be zero-config | LOW | Single `docker-compose.yml` with PostgreSQL, auto-create schema, load data. Volume persistence optional but nice. |
| **Idempotent loading (re-runnable without duplicates)** | Data engineers will run the pipeline multiple times during development and testing; duplicates destroy trust instantly | MEDIUM | Use UPSERT (INSERT ON CONFLICT UPDATE) keyed on resource IDs. Every Particle resource has a stable ID field. Delete-then-insert is acceptable alternative but UPSERT is cleaner. |
| **Schema-resilient loading** | Particle may add fields, customers may have partial data (empty arrays for some resource types); pipeline must not crash on schema variations | MEDIUM | Handle missing keys gracefully (empty table, no error). Handle extra fields (log warning, skip or add column). Handle null values in expected fields. |
| **Pre-built SQL analytics queries** | Customers need immediate proof of value; raw tables alone are not enough to demonstrate "so what?" | MEDIUM | Include 10-15 ready-to-run SQL queries covering clinical and operational analytics. Queries must work against the sample data included in the repo. |
| **Clear README with setup instructions** | Accelerator must work from clean checkout; instructions are the product as much as the code | LOW | Step-by-step: clone, configure, run. Separate paths for Docker/local vs BigQuery/cloud. Expected output shown. |
| **Sample data included** | Users must see value without Particle API credentials; the existing `flat_data.json` (904KB, 1 patient, 21 resource types) fulfills this | LOW | Already exists in repo. Must cover enough resource types to make analytics queries meaningful. |
| **Environment variable configuration** | Standard for secrets (API keys, DB credentials); no config files with secrets | LOW | `PARTICLE_CLIENT_ID`, `PARTICLE_CLIENT_SECRET`, `PARTICLE_SCOPE_ID` for API mode. `DATABASE_URL` or individual `PG_*` vars for PostgreSQL. `GOOGLE_PROJECT_ID`, `BQ_DATASET` for BigQuery. |
| **Error messages that tell you what to fix** | Data engineers debugging pipeline failures need actionable errors, not stack traces | LOW | "Table 'labs' load failed: column 'lab_value_quantity' expected numeric, got string 'N/A'. Row 47." not "ValueError: could not convert string to float" |

### Differentiators (Competitive Advantage)

Features that set the accelerator apart. Not required, but create delight and faster time-to-value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **BigQuery cloud mode with Terraform** | Most healthcare data tools only do one destination; supporting both local PostgreSQL AND cloud BigQuery with IaC makes this production-ready, not just a demo | HIGH | Terraform module creates dataset + tables. Separate Python loader for BigQuery (google-cloud-bigquery client). Same DDL definitions drive both PostgreSQL and BigQuery schema. |
| **Pre-built clinical analytics queries** | Go beyond raw tables to deliver actual clinical insights: medication adherence gaps, lab trend analysis, encounter utilization, problem prevalence. Customers see the "so what?" immediately. | MEDIUM | Categories: (1) Patient summary, (2) Encounter patterns, (3) Lab trends over time, (4) Medication timeline, (5) Problem list with onset tracking, (6) Vital sign trends. Must work on both PostgreSQL and BigQuery SQL dialects. |
| **Pre-built operational analytics queries** | Healthcare ops teams care about data completeness, source coverage, and record freshness. Queries like "which sources contributed data?" and "how many records per resource type?" answer operational questions. | LOW | Leverage the `sources`, `recordSources`, and `transitions` tables. These are unique to Particle and not available in generic FHIR tools. |
| **Data lineage / provenance tracking** | Particle's `recordSources` and `sources` tables link every clinical record to its originating data source. Exposing this in queryable form is unique value that FHIR-generic tools lack. | LOW | Already in the Flat API response. Just need DDL + load + example queries. |
| **AI citations as queryable data** | Particle's `aICitations` and `aIOutputs` are unique resources not found in any other health data API. Making these queryable lets customers build AI-augmented clinical workflows. | LOW | 542 citations and 22 outputs in sample data. DDL + load is straightforward. Analytics queries linking citations to source documents are the differentiator. |
| **Schema auto-detection from JSON** | Instead of hand-coding DDL for 21 tables, introspect the Flat JSON and generate DDL automatically. Handles schema evolution when Particle adds new resource types or fields. | MEDIUM | Walk JSON keys, infer types from values (string, numeric, boolean, timestamp, array). Generate CREATE TABLE statements. Run once to bootstrap, then use generated DDL going forward. |
| **Data quality report** | After loading, produce a summary: records loaded per table, null percentages for key fields, date ranges covered, potential data quality issues. Builds trust. | MEDIUM | Run post-load validation queries. Output as terminal table or markdown file. Flag issues like "labs table: 23% of lab_value fields are null" or "encounters: date range 2023-01-15 to 2024-08-22". |
| **Transition-of-care analytics** | Particle's `transitions` resource tracks patient movement between care settings (ED, inpatient, outpatient). This is high-value operational data most platforms lack. | LOW | DDL + load + queries for: discharge disposition distribution, average length of stay, readmission patterns, admitting vs discharge diagnosis concordance. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems. Deliberately NOT building these keeps the accelerator focused and maintainable.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Web UI / dashboard** | "Can I see the data in a browser?" | Massively increases scope (frontend framework, hosting, auth, state management). Customers have their own BI tools (Metabase, Looker, Tableau). Building a UI competes with their existing stack instead of complementing it. | Provide SQL queries that work in any SQL client. Include a `docker-compose` option with Adminer or pgAdmin for those who want a UI. |
| **Real-time streaming / CDC pipeline** | "Can it update automatically when new data arrives?" | Particle's API is request-response (query, wait, retrieve), not a streaming source. Building CDC/streaming adds Kafka/pubsub complexity for a batch-oriented data source. Over-engineers the problem. | Batch pipeline that can be re-run (idempotent). Provide a cron/scheduler example for periodic refreshes. |
| **FHIR R4 resource parsing** | "Can it also handle FHIR format?" | Flat format already IS the analytics-friendly projection of FHIR. Parsing FHIR R4 bundles requires fhir.resources library, deeply nested JSON traversal, and creates a parallel code path that doubles maintenance. Particle's sandbox does not support FHIR endpoint. | Focus on Flat format exclusively. Note that Flat IS derived from FHIR R4. If users need FHIR, point them to existing fhir.resources library. |
| **Multi-database support beyond PG/BQ** | "Can it also load to Snowflake / Redshift / Databricks?" | Each database has different DDL syntax, different Python drivers, different auth patterns. Supporting N databases creates N maintenance burdens. | Design the DDL generation to be extensible (template-based), but only ship PostgreSQL and BigQuery. Document how to add new targets. |
| **Orchestration framework (Airflow, Dagster, Prefect)** | "Can it run on a schedule with retries and monitoring?" | Adding an orchestration framework turns a simple accelerator into an infrastructure project. Customers who need orchestration already have it. | Provide a simple Python entry point that orchestrators can call. Include example cron job or Cloud Scheduler config. Document "how to plug this into Airflow" as a one-pager. |
| **Data transformation / dbt models** | "Can it transform the raw data into analytics-ready models?" | dbt adds a build system, a new language (Jinja SQL), project structure, and opinions about staging/marts that may conflict with customer's existing dbt setup. | Ship raw table loads + pre-built SQL queries. The queries serve as "virtual views" customers can promote to dbt models in their own project. |
| **HIPAA compliance features** | "Is this HIPAA compliant?" | HIPAA compliance is an organizational property, not a tool feature. Adding encryption-at-rest, audit logging, access controls, BAA management creates false security theater in a starter kit. | Document security considerations clearly. Note that Docker local mode is for development only. Note that BigQuery mode inherits GCP's HIPAA compliance. Recommend customers add their own access controls. |
| **Multi-patient batch processing** | "Can it load 10,000 patients at once?" | Batch processing at scale requires different architecture (parallel workers, rate limiting, progress tracking, partial failure handling). This is production infrastructure, not starter kit territory. | Design for single-patient-at-a-time with clear extension points. Provide a simple loop wrapper for small batches. Document "scaling to production" considerations. |
| **Schema migration tooling (Alembic, Flyway)** | "Can it migrate my schema when Particle adds fields?" | Migration tools add dependency management, migration history tables, up/down scripts, and version tracking overhead inappropriate for a starter kit. | Schema-resilient loading handles new fields gracefully. DDL generation can be re-run to produce updated schema. Provide a "schema diff" utility that shows what changed. |
| **Config file support (YAML/TOML/JSON)** | "Can I put my settings in a config file?" | Adds a config parsing dependency, a config file format decision, config validation, and a place where secrets might accidentally get committed. | Environment variables only, consistent with the existing particle-health-starters pattern. Provide a `.env.example` file for documentation. |

## Feature Dependencies

```
[Docker PostgreSQL local mode]
    |-- requires --> [DDL generation for all 21 resource types]
    |-- requires --> [Dual ingestion mode (file load path)]
    |-- requires --> [Idempotent loading]
    |-- requires --> [Schema-resilient loading]
    |-- enhances --> [Pre-built SQL analytics queries]

[BigQuery cloud mode with Terraform]
    |-- requires --> [DDL generation for all 21 resource types]
    |-- requires --> [Dual ingestion mode (both paths)]
    |-- requires --> [Idempotent loading]
    |-- requires --> [Schema-resilient loading]
    |-- enhances --> [Pre-built SQL analytics queries]

[Pre-built SQL analytics queries]
    |-- requires --> [DDL generation] (tables must exist)
    |-- requires --> [Sample data included] (queries need data to run against)
    |-- requires --> [At least one ingestion mode working]

[Schema auto-detection from JSON]
    |-- enhances --> [DDL generation for all 21 resource types]
    |-- enhances --> [Schema-resilient loading]

[Data quality report]
    |-- requires --> [Idempotent loading] (must have loaded data)
    |-- enhances --> [Pre-built SQL analytics queries]

[Dual ingestion mode]
    |-- file path requires --> [Sample data included]
    |-- API path requires --> [particle-health-starters SDK] (existing v1.0)

[AI citations as queryable data]
    |-- requires --> [DDL generation] (aICitations + aIOutputs tables)
    |-- enhances --> [Pre-built SQL analytics queries]

[Transition-of-care analytics]
    |-- requires --> [DDL generation] (transitions table)
    |-- enhances --> [Pre-built SQL analytics queries]
```

### Dependency Notes

- **DDL generation is the foundation:** Every other feature depends on tables existing. Build this first.
- **File-based ingestion enables "clean checkout" demo:** This must work before API mode, because it proves value without credentials.
- **PostgreSQL local mode before BigQuery cloud mode:** Local mode is simpler, validates the pipeline, and gives faster iteration. BigQuery adds Terraform, GCP auth, and network considerations.
- **Analytics queries depend on loaded data:** Cannot be tested or demonstrated until at least file ingestion into PostgreSQL works end-to-end.
- **Schema auto-detection enhances but does not replace DDL:** Can generate DDL automatically, but hand-tuned DDL with correct types and constraints is more reliable for production. Auto-detection is a developer convenience, not a runtime requirement.

## MVP Definition

### Launch With (v1)

Minimum viable product -- what is needed for the accelerator to deliver value from a clean checkout.

- [ ] **DDL generation for all 21 Particle Flat resource types** -- without tables, nothing else works
- [ ] **File-based ingestion into PostgreSQL** -- proves the pipeline end-to-end without API credentials
- [ ] **Docker Compose for local PostgreSQL** -- zero-config database setup
- [ ] **Idempotent UPSERT loading** -- re-runnable without duplicates, essential for trust
- [ ] **Schema-resilient loading** -- handles empty arrays, missing fields, and nulls without crashing
- [ ] **10-15 pre-built SQL analytics queries** -- clinical + operational, demonstrates "so what?"
- [ ] **Sample data included** -- already exists (flat_data.json, 904KB)
- [ ] **README with setup instructions** -- clone, docker compose up, run loader, run queries
- [ ] **Actionable error messages** -- tells you what went wrong and how to fix it

### Add After Validation (v1.x)

Features to add once core file-to-PostgreSQL pipeline is working and validated.

- [ ] **API live ingestion mode** -- trigger: customers want to move beyond sample data to their own patients
- [ ] **BigQuery cloud mode with Terraform** -- trigger: customers ready to move from local demo to cloud deployment
- [ ] **Schema auto-detection from JSON** -- trigger: Particle adds new resource types or fields and DDL needs updating
- [ ] **Data quality report** -- trigger: customers loading real data need to verify completeness and accuracy
- [ ] **AI citation analytics queries** -- trigger: customers using Particle's AI features want to query citation data

### Future Consideration (v2+)

Features to defer until the accelerator has proven adoption.

- [ ] **Transition-of-care analytics** -- defer because transitions data is specialized and not all customers have it
- [ ] **Multi-patient batch wrapper** -- defer because it requires production-grade error handling and rate limiting
- [ ] **BigQuery SQL dialect variants of all queries** -- defer because most queries are standard SQL; handle dialect differences only where needed
- [ ] **Orchestration integration examples (Airflow, etc.)** -- defer because customers who need orchestration already have it and can call the Python entry point
- [ ] **Additional database targets** -- defer because PostgreSQL + BigQuery covers 90%+ of the target audience

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| DDL generation for all 21 types | HIGH | MEDIUM | P1 |
| File-based ingestion (PostgreSQL) | HIGH | MEDIUM | P1 |
| Docker Compose local mode | HIGH | LOW | P1 |
| Idempotent UPSERT loading | HIGH | MEDIUM | P1 |
| Schema-resilient loading | HIGH | MEDIUM | P1 |
| Pre-built SQL analytics queries | HIGH | MEDIUM | P1 |
| Sample data included | HIGH | LOW (already exists) | P1 |
| README / setup docs | HIGH | LOW | P1 |
| Actionable error messages | HIGH | LOW | P1 |
| API live ingestion mode | HIGH | MEDIUM | P2 |
| BigQuery cloud mode + Terraform | HIGH | HIGH | P2 |
| Schema auto-detection from JSON | MEDIUM | MEDIUM | P2 |
| Data quality report | MEDIUM | MEDIUM | P2 |
| AI citation analytics | MEDIUM | LOW | P2 |
| Data lineage queries (recordSources) | MEDIUM | LOW | P2 |
| Transition-of-care analytics | MEDIUM | LOW | P3 |
| Multi-patient batch wrapper | LOW | MEDIUM | P3 |
| BigQuery SQL dialect variants | LOW | MEDIUM | P3 |
| Orchestration integration docs | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch -- accelerator is incomplete without these
- P2: Should have, add after core pipeline validated
- P3: Nice to have, future consideration based on customer demand

## Competitor Feature Analysis

| Feature | Redox + Databricks | Google Healthcare Data Engine | Microsoft Healthcare Data Foundations | Our Approach (Particle Connect) |
|---------|-------------------|------------------------------|--------------------------------------|-------------------------------|
| Data source | Multiple EHRs via Redox | FHIR stores, HL7 | FHIR, HL7, DICOM | Particle Health Flat API (single query, nationwide network) |
| Setup complexity | High (Spark, Databricks, Redox) | High (GCP, FHIR store, Cloud Healthcare API) | High (Azure, Fabric, healthcare data solutions) | Low (Docker + Python, works from clean checkout) |
| Time to first query | Days-weeks | Days-weeks | Days-weeks | Minutes (sample data + pre-built queries) |
| Target user | Data engineers with cloud expertise | GCP data engineers | Azure data engineers | Any data/analytics engineer or app developer |
| Analytics included | Build your own | Accelerator use cases (care management, etc.) | Pre-built Power BI dashboards | Pre-built SQL queries (portable, no vendor lock-in) |
| Local development | Not supported | Not supported | Not supported | Docker Compose, zero cloud dependency |
| Cost to evaluate | Databricks + Redox licenses | GCP billing | Azure billing | Free (Docker + sample data) |
| Idempotent loading | Depends on implementation | Depends on implementation | Depends on implementation | Built-in UPSERT on resource IDs |
| Schema management | Delta Lake / Unity Catalog | FHIR store schema | Healthcare data model | Auto-generated DDL from Flat API structure |
| AI features | Separate AI/ML pipeline | Vertex AI integration | Azure AI integration | Particle AI citations queryable as tables |

**Our competitive advantage:** The accelerator wins on time-to-first-value and simplicity. Enterprise competitors require cloud accounts, licenses, and days of setup. We deliver queryable clinical data in minutes from a clean checkout with zero cost. The pre-built SQL queries mean customers can demonstrate value in their first meeting, not their first sprint.

## Analytics Query Categories

Based on the 21 resource types in the Particle Flat API and common healthcare analytics patterns, the pre-built queries should cover these categories.

### Clinical Analytics (high value, high demand)

1. **Patient summary** -- Demographics, conditions, medications, allergies for a single patient
2. **Active problem list** -- Current conditions with onset dates and clinical status
3. **Medication timeline** -- Medications with start/end dates, dosage, and status
4. **Lab results over time** -- Lab values trended by date, flagged abnormals
5. **Vital sign trends** -- Blood pressure, heart rate, temperature, BMI over time
6. **Encounter history** -- Chronological encounters with type, location, and duration
7. **Care team** -- Practitioners involved in care with roles and specialties

### Operational Analytics (unique to Particle, high differentiation)

8. **Data completeness scorecard** -- Records per resource type, percentage populated
9. **Source coverage** -- Which data sources contributed records, by type
10. **Record freshness** -- Most recent records per resource type and source
11. **Data provenance** -- Trace any clinical record back to its originating source
12. **AI output summary** -- AI-generated insights with citation counts and source documents

### Cross-cutting Analytics

13. **Encounter-to-labs join** -- Labs ordered during specific encounters
14. **Medication-problem correlation** -- Medications mapped to the problems they treat
15. **Procedures by encounter** -- Procedures performed during each encounter with practitioners

## Sources

- [Particle Health Data Retrieval APIs](https://docs.particlehealth.com/docs/data-retrieval-apis) -- Flat format documentation, dataset types (HIGH confidence)
- [Particle Health Patient Data APIs](https://docs.particlehealth.com/docs/patient-data-apis) -- API reference (HIGH confidence)
- Actual `flat_data.json` sample data (904KB, 21 resource types) from project repo -- direct inspection of field structures (HIGH confidence)
- [Integrate.io: Data Pipelines for Healthcare](https://www.integrate.io/blog/data-pipelines-healthcare/) -- Healthcare ETL patterns (MEDIUM confidence)
- [KDnuggets: Building Data Pipelines That Don't Break](https://www.kdnuggets.com/the-complete-guide-to-building-data-pipelines-that-dont-break) -- Idempotency, schema versioning, data quality monitoring (MEDIUM confidence)
- [Google Cloud: Healthcare Data Engine Accelerators](https://cloud.google.com/blog/topics/healthcare-life-sciences/introducing-healthcare-data-engine-accelerators) -- Competitor feature analysis (MEDIUM confidence)
- [Microsoft: Healthcare Data Foundations](https://learn.microsoft.com/en-us/industry/healthcare/healthcare-data-solutions/healthcare-data-foundations) -- Competitor feature analysis (MEDIUM confidence)
- [Databricks + Redox Partnership](https://www.databricks.com/blog/new-partnership-redox-and-how-we-unlock-healthcare-data-drive-advanced-analytics) -- Competitor feature analysis (MEDIUM confidence)
- [Healthcare SQL Analytics Project](https://github.com/yuan-code/Healthcare_Data_in_SQL_and_Visualization_in_Tableau) -- Example clinical analytics queries (MEDIUM confidence)
- [SQL on FHIR v2](https://build.fhir.org/ig/FHIR/sql-on-fhir-v2/) -- Standard approach to tabular views of FHIR data (MEDIUM confidence)
- [Airbyte: Idempotency in Data Pipelines](https://airbyte.com/data-engineering-resources/idempotency-in-data-pipelines) -- UPSERT and deduplication patterns (MEDIUM confidence)
- [Terraform Google BigQuery Module](https://github.com/terraform-google-modules/terraform-google-bigquery) -- BigQuery IaC patterns (HIGH confidence)
- [Docker PostgreSQL Setup Guide](https://utho.com/blog/postgresql-docker-setup/) -- Local development patterns (MEDIUM confidence)

---
*Feature research for: Healthcare data pipeline accelerator (Particle Health Flat API to PostgreSQL/BigQuery)*
*Researched: 2026-02-07*
