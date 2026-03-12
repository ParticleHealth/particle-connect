# End-to-End One-Shot Test Prompts

These prompts test the repo's ability to guide a new user from zero to a working result in a single prompt. Each prompt covers a different combination of Particle API endpoints, data formats, and storage/analysis targets.

---

## Prompt 1: CCDA Retrieval → GCS Bucket

> I'm new to this repo. I have Particle sandbox credentials (client ID, client secret, and scope ID). I want to:
> 1. Register a test patient using the sandbox demographics
> 2. Submit a query and wait for it to complete
> 3. Retrieve the CCDA XML documents for that patient
> 4. Store the CCDA files in a Google Cloud Storage bucket called `my-ccda-archive` with a folder structure of `/{patient_id}/{timestamp}/`
>
> Write the complete Python script, tell me what dependencies to install, and walk me through running it.

**Tests**: Patient registration → query flow → CCDA retrieval → GCS integration (external to repo)

---

## Prompt 2: Flat Data → PostgreSQL + Analytical Queries

> I just cloned this repo and want to pull flat data from the Particle API and load it into a local PostgreSQL database. Specifically:
> 1. Set up the environment and install dependencies
> 2. Register the sandbox test patient and run a query
> 3. Retrieve the flat JSON data
> 4. Generate the PostgreSQL DDL and create all 21 tables in my local Postgres (host: localhost, db: particle_clinical)
> 5. Load the flat data into the tables
> 6. Run SQL queries to find: (a) all active medications for the patient, (b) encounters in the last year, and (c) any lab results with abnormal flags
>
> Give me everything I need — scripts, SQL, and step-by-step instructions.

**Tests**: Full query flow → flat data retrieval → DDL generation → Postgres loading → analytical SQL

---

## Prompt 3: Flat Data → DuckDB Analytics (Happy Path)

> I have no Particle credentials and just want to explore the sample data. Walk me through:
> 1. Setting up the analytics quickstart with the sample flat data
> 2. Loading it into DuckDB
> 3. Running all 15 pre-built queries and explaining what each one tells me
> 4. Writing 3 custom queries: one for medication-problem correlations, one for care gaps (patients without recent encounters), and one for data completeness scoring per patient
>
> I want to do this entirely locally with zero cloud setup.

**Tests**: No-credential path → sample data → DuckDB pipeline → pre-built queries → custom SQL authoring

---

## Prompt 4: Signal/ADT Webhooks → Real-Time Monitoring Pipeline

> I want to set up real-time patient monitoring using Particle's Signal/ADT webhooks. Using the sandbox:
> 1. Register a patient and subscribe them to MONITORING
> 2. Set up a local webhook receiver to capture CloudEvents notifications
> 3. Trigger an ADMIT_TRANSITION_ALERT and a DISCHARGE_TRANSITION_ALERT in the sandbox
> 4. Parse the incoming webhook payloads, verify the HMAC signatures, and extract the transition details
> 5. Store each alert as a row in a local SQLite database with columns for event_type, patient_id, facility, timestamp, and raw_payload
> 6. Print a summary of all captured alerts
>
> Give me the complete working code and instructions.

**Tests**: Patient registration → Signal subscription → webhook receiver → sandbox trigger → payload parsing → HMAC verification → SQLite storage

---

## Prompt 5: Full Pipeline — Query to BigQuery with Terraform

> I want to stand up an end-to-end clinical data pipeline from Particle to BigQuery. Help me:
> 1. Use the Terraform configs in this repo to provision the BigQuery dataset and all 21 tables in my GCP project `my-health-project`
> 2. Register the sandbox test patient and pull their flat data via the API
> 3. Load the flat data into BigQuery using the analytics pipeline
> 4. Run the pre-built queries against BigQuery
> 5. Create a BigQuery view that joins patients, encounters, problems, and medications into a single denormalized patient-360 view
>
> Walk me through every step including `terraform apply`, Python setup, and the BigQuery queries.

**Tests**: Terraform IaC → full query flow → BigQuery loader → pre-built queries → custom view creation

---

## Prompt 6: Management UI → Project Setup → First Query

> I'm an admin setting up Particle for my organization. Walk me through:
> 1. Spinning up the Management UI using Docker Compose
> 2. Creating a new project and service account through the UI
> 3. Generating credentials for the service account
> 4. Using those credentials to register a patient and run a query via the Python SDK
> 5. Retrieving both the flat data AND CCDA for the patient
> 6. Showing me how to compare what's in the flat JSON vs the raw CCDA XML
>
> I want to go from zero to seeing clinical data.

**Tests**: Docker Compose → Management UI → credential lifecycle → SDK query → dual-format retrieval → data comparison

---

## Prompt 7: Document Submission + Retrieval Round-Trip

> I have a C-CDA XML file that I want to submit to Particle and then verify it's queryable. Help me:
> 1. Take the sample CCDA from the repo (or generate a minimal valid one)
> 2. Submit it via the Document API (POST /api/v1/documents)
> 3. Register the corresponding patient and submit a query
> 4. Retrieve the flat data and CCDA to confirm the document was ingested
> 5. Compare the submitted document against the retrieved one
>
> Give me the full script with error handling.

**Tests**: Document submission API → patient registration → query flow → retrieval → round-trip verification

---

## Prompt 8: Multi-Patient Batch Processing → CSV Report

> I need to process multiple patients in batch. Using the sandbox:
> 1. Register 3 test patients (use the sandbox seeded demographics)
> 2. Submit queries for all 3 in parallel
> 3. Poll for all queries to complete
> 4. Retrieve flat data for each patient
> 5. Generate a CSV summary report with one row per patient containing: patient name, number of encounters, number of active medications, number of problems, most recent encounter date, and data completeness score (% of non-null fields)
>
> Optimize for speed with concurrent requests. Give me the complete async Python script.

**Tests**: Batch registration → parallel queries → concurrent polling → multi-patient flat data → CSV report generation

---

## Prompt 9: Flat Data → S3 Data Lake with Partitioning

> I want to build a clinical data lake on S3. Help me:
> 1. Register the sandbox patient and pull flat data
> 2. Transform the flat JSON into partitioned Parquet files organized by: `s3://my-clinical-lake/{table_name}/patient_id={id}/data.parquet`
> 3. Write a script that uploads these to S3
> 4. Create an AWS Glue catalog entry (or provide the DDL) so I can query the data with Athena
> 5. Give me 5 sample Athena SQL queries for clinical analysis
>
> Include the complete Python script using boto3 and pyarrow.

**Tests**: Query flow → flat data → Parquet transformation → S3 upload → Glue/Athena integration

---

## Prompt 10: Webhook Notifications → Slack Alerts

> I want to get Slack notifications whenever a patient has a care transition. Set up:
> 1. A webhook receiver that listens for Particle transition alert CloudEvents
> 2. HMAC signature verification on incoming webhooks
> 3. Parse the transition type (admit/discharge/transfer) and patient details
> 4. Format and send a Slack message to channel #patient-alerts with: patient name, transition type, facility, and timestamp
> 5. Test the whole thing by triggering sandbox alerts
>
> Give me a complete FastAPI app with a Slack integration and the sandbox test script.

**Tests**: Webhook receiver → HMAC verification → payload parsing → Slack API integration → sandbox trigger testing

---

## Evaluation Criteria

For each prompt, evaluate:

| Criteria | What to look for |
|----------|-----------------|
| **Setup guidance** | Does it correctly identify which subproject to use, install deps, and configure `.env`? |
| **API accuracy** | Does it use the correct endpoints, headers, auth flow, and request/response shapes? |
| **Sandbox awareness** | Does it use sandbox-appropriate patients and handle sandbox limitations (e.g., no FHIR)? |
| **Error handling** | Does it account for common gotchas (query polling, 404 during propagation, state vs status)? |
| **Code quality** | Is the generated code runnable, well-structured, and using repo patterns (SDK vs raw HTTP)? |
| **Completeness** | Does it deliver everything needed to go from zero to working result? |
| **Doc discovery** | Did it find and use the relevant agent-documentation, troubleshooting guides, and sample code? |
