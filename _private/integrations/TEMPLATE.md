# Integration: {CLIENT_NAME}

> Status: DISCOVERY | SPECIFICATION | DEVELOPMENT | TESTING | PRODUCTION

---

## Phase 1: Discovery

### What Data Do They Need from Particle?

| Need | Format | Particle Support |
|------|--------|-----------------|
| Patient demographics | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Lab results | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Medications | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Problems/Conditions | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Encounters | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Real-time ADT alerts | Signal webhooks | CloudEvents 1.0, sandbox trigger available |
| Document submission | C-CDA XML / PDF | POST /api/v1/documents |
| Other: | | |

### Data Direction
- [ ] Particle → Client (query + retrieve)
- [ ] Client → Particle (document submission)
- [ ] Bidirectional
- [ ] Real-time events (Signal webhooks)

### Volume and Frequency
- **Patient volume**: ___ patients (one-time backfill? ongoing?)
- **Query frequency**: One-time | Nightly batch | On-demand | Real-time triggers
- **Concurrency model**: Sequential | Parallel (async batch) | Event-driven (webhook)
- **Expected data size per patient**: Small (<100 records) | Medium (100-1K) | Large (1K+)

---

## Phase 2: Architecture

### End-to-End Pipeline Pattern

> Pick the pattern that matches the integration, or combine patterns for hybrid flows.

#### Pattern A: Query → Storage (Batch / On-Demand)
```
Particle Query Flow API ──► Flat JSON / CCDA / FHIR ──► Storage Target
```
- Register patient → submit query → poll (2-5 min) → retrieve data → transform → load
- **Best for**: Data warehouses, data lakes, analytics, EHR backfill

#### Pattern B: Webhooks → Event Processing (Real-Time)
```
Particle Signal API ──► CloudEvents webhook ──► Event processor ──► Downstream action
```
- Subscribe patient to MONITORING → receive ADT alerts → verify HMAC → parse → act
- **Best for**: Care coordination, alerting, real-time dashboards, notifications

#### Pattern C: Document Submission → Verification (Inbound)
```
Client system ──► C-CDA XML ──► Particle Document API ──► Query to verify ingestion
```
- Submit document → register patient → query → retrieve to confirm round-trip
- **Best for**: HIE contribution, data sharing, document exchange

#### Pattern D: Full Lifecycle (Bidirectional + Real-Time)
```
Client ──► Document API ──► Particle ──► Query API ──► Client storage
                                    └──► Signal API ──► Webhook receiver ──► Alerts
```
- Combines submission, retrieval, and real-time monitoring
- **Best for**: Full platform integrations, population health, care management

**Selected pattern(s)**: ___

### Data Flow Diagram

```
┌──────────────────┐         ┌─────────────────────┐         ┌──────────────────┐
│  Client System   │         │  Integration Layer   │         │  Particle Health │
│                  │◄────────│                      │────────►│                  │
│  {system_name}   │         │  {middleware_type}    │         │  Query Flow API  │
│                  │ {transport} │                   │ HTTPS   │  Signal API      │
└──────────────────┘         └─────────────────────┘         │  Document API    │
                                                              └──────────────────┘
```

### Integration Layer

- **Type**: Direct SDK | Custom middleware | ETL pipeline | Webhook relay | Managed service
- **Runtime**: Python script | FastAPI service | Cloud Function | Airflow DAG | Docker container | Other
- **Orchestration** (if batch): Sequential | Async parallel (asyncio) | Queue-based (Celery/SQS)

### Storage Target

> Where does the Particle data land? Pick one or more.

| Target | Use Case | Setup Reference |
|--------|----------|----------------|
| **DuckDB** (local) | Quick exploration, local analytics, zero cloud setup | `particle-analytics-quickstarts/` — sample data + 15 pre-built queries |
| **PostgreSQL** | Relational storage, application backend, SQL analytics | Generate DDL with `observatory-generate-ddl`, 21-table schema |
| **BigQuery** (GCP) | Cloud-scale analytics, patient-360 views | Terraform in `terraform/`, BigQuery loader in `observatory/bq_loader.py` |
| **GCS bucket** (GCP) | CCDA/document archival, raw data lake | Store by `/{patient_id}/{timestamp}/` or `/{format}/{date}/` |
| **S3** (AWS) | Data lake with Parquet partitioning, Athena queryable | Partition by `/{table_name}/patient_id={id}/data.parquet` |
| **SQLite** (local) | Lightweight event store for webhook alerts | Single-file DB, good for alert history and audit trail |
| **Downstream API** | Push to client REST endpoint, EHR, or message queue | Transform Particle data → client schema → POST/publish |
| **Slack / PagerDuty** | Alert routing for ADT transitions | Webhook receiver → parse event → format → send notification |
| **Other**: | | |

**Selected target(s)**: ___

### Particle Auth
- **Credential level**: Project (service account) | Organization
- **Environment**: Sandbox | Production
- **Scope ID**: projects/{id}
- **Credential storage**: .env | Vault | Cloud secret manager

### Client-Side Transport
- **How data reaches client system**: REST API | Database insert | File drop (SFTP/S3/GCS) | Message queue | Webhook callback | Other
- **Client endpoint URL** (if applicable):
- **Error handling**: Retry with backoff? Dead letter queue? Alert on failure?

---

## Phase 3: Detailed Design

### Query Flow Design (if using Pattern A or D)

| Step | Component | Details |
|------|-----------|---------|
| 1. Register patient | SDK `register_patient()` or `POST /api/v2/patients` | Demographics: given_name, family_name, DOB, gender, address |
| 2. Submit query | SDK `submit_query()` or `POST /api/v2/patients/{id}/query` | Returns immediately, processing takes 2-5 min |
| 3. Poll for completion | SDK `wait_for_query()` with exponential backoff | States: PENDING → PROCESSING → COMPLETE / PARTIAL / FAILED |
| 4. Retrieve data | SDK `get_flat()` / `get_ccda()` / `get_fhir()` | Flat = JSON, CCDA = ZIP of XML, FHIR = Bundle (prod only) |
| 5. Transform | Map Particle schema → target schema | 21 flat tables, or raw CCDA XML |
| 6. Load | Write to storage target | Idempotent: DELETE + INSERT per patient_id |

- **Batch strategy** (if multi-patient): Register all → submit all → poll all concurrently → retrieve all → bulk load
- **Concurrency limit**: ___ parallel queries (respect Particle rate limits)
- **Error recovery**: Retry failed queries? Skip and log? Alert?

### Webhook Design (if using Pattern B or D)

| Step | Component | Details |
|------|-----------|---------|
| 1. Subscribe patient | `POST /api/v1/patients/{id}/subscriptions` | Type: MONITORING, callback_url required |
| 2. Receive event | HTTPS endpoint (public, TLS) | CloudEvents 1.0 format |
| 3. Verify signature | HMAC SHA-256 on request body | Secret from Particle dashboard |
| 4. Parse payload | Extract event type, patient ID, transition details | Types: admit, discharge, transfer, new encounter, etc. |
| 5. Act | Route to storage / alert / downstream API | Based on `type` field in CloudEvents envelope |

- **Webhook receiver**: FastAPI | Flask | Cloud Function | Lambda | Other
- **Supported event types**:
  - [ ] Transition alerts (admit/discharge/transfer)
  - [ ] HL7v2 ADT messages
  - [ ] Query complete notifications
  - [ ] New encounter alerts
  - [ ] AI output ready
  - [ ] Patient consent updated
  - [ ] Medication fills

### Document Submission Design (if using Pattern C or D)

| Step | Component | Details |
|------|-----------|---------|
| 1. Prepare document | Valid C-CDA XML or PDF | Must include patient demographics in header |
| 2. Submit | `POST /api/v1/documents` | Multipart upload |
| 3. Verify ingestion | Register patient → query → retrieve | Confirm submitted data appears in results |

### Data Transform and Loading

> Define how Particle data maps to the target system.

- **Schema approach**: Use Particle's 21-table flat schema as-is | Map to client schema | Denormalize into views
- **Key transforms needed**:
  - [ ] Field renames (Particle field → client field)
  - [ ] Type conversions (e.g., lab_value TEXT → NUMERIC)
  - [ ] Date format changes (YYYY-MM-DD → ?)
  - [ ] Code system mapping (ICD-10, SNOMED, RxNorm → client codes)
  - [ ] Denormalization (e.g., patient-360 view joining patients + encounters + problems + medications)
- **Idempotency strategy**: DELETE + INSERT per patient_id | Upsert on primary key | Append with dedup

---

## Phase 4: Test Scenario Mapping

> Map client test cases to Particle sandbox capabilities.

| Test Case | Sandbox Approach | Expected Outcome |
|-----------|-----------------|-----------------|
| Basic flat data retrieval | Register Elvira Valadez-Nucleus → query → get flat | ~1,187 records across 16 resource types |
| CCDA retrieval | Same patient → get CCDA | ZIP file with C-CDA XML documents |
| Empty data handling | Register with arbitrary demographics | Query completes, flat returns `{}` |
| Multi-patient batch | Register 3 sandbox patients → parallel queries | All complete, flat data for each |
| Signal ADT alert | Subscribe patient → trigger ADMIT_TRANSITION_ALERT | CloudEvents webhook delivered to callback_url |
| Signal discharge alert | Subscribe patient → trigger DISCHARGE_TRANSITION_ALERT | CloudEvents webhook with discharge details |
| Webhook HMAC verification | Receive webhook → validate signature | Signature matches, payload trusted |
| Document submission round-trip | Submit C-CDA → query same patient → retrieve | Submitted data appears in retrieval results |
| Re-registration (idempotent) | Same patient_id + same demographics | Returns same particle_patient_id |
| Re-registration (overlay error) | Same patient_id + different demographics | 422 overlay error |
| Query timeout / failure | Patient with no network data | Query completes with FAILED or empty results |
| Storage target loading | Load flat data into target (DuckDB/Postgres/BigQuery/S3) | All 21 tables populated, queries return expected results |
| End-to-end latency | Register → query → retrieve → load → query target | Measure total pipeline time |

---

## Implementation Checklist

- [ ] Particle credentials provisioned and stored securely
- [ ] `.env` configured (client_id, client_secret, scope_id, base_url)
- [ ] Integration layer built and tested against sandbox
- [ ] Storage target provisioned (tables/buckets/datasets created)
- [ ] Data transform logic implemented and validated
- [ ] Webhook receiver deployed with HMAC verification (if applicable)
- [ ] Error handling: retries, dead letters, alerting
- [ ] Batch/concurrency tested at expected volume
- [ ] Idempotency verified (re-run produces same result, no duplicates)
- [ ] End-to-end test passing in sandbox
- [ ] Production credentials provisioned
- [ ] Production deployment and smoke test

---

## Implementation Notes

> Add notes as development progresses. Reference specific files/commits.

-
