---
phase: 04-cloud-mode
plan: 01
subsystem: infra
tags: [terraform, bigquery, gcp, iam, service-account, hcl]

# Dependency graph
requires:
  - phase: 01-schema-foundation
    provides: "DDL with 21 table schemas (16 data + 5 empty) used as source of truth for Terraform locals"
provides:
  - "Complete Terraform module for BigQuery dataset + 21 tables + service account + IAM"
  - "Customer-configurable variables (project_id, dataset_name, region)"
  - "Service account with minimum permissions (dataEditor + jobUser)"
affects: [04-cloud-mode plan 02 (BigQuery loader needs dataset/tables to exist), 04-cloud-mode plan 03 (CLI wiring references Terraform outputs)]

# Tech tracking
tech-stack:
  added: ["hashicorp/google ~> 7.0 (Terraform provider)"]
  patterns: ["for_each with locals map for 21 identical-pattern tables", "jsonencode schema for all-STRING BigQuery columns", "dataset-level vs project-level IAM scoping"]

key-files:
  created:
    - "particle-flat-observatory/terraform/main.tf"
    - "particle-flat-observatory/terraform/variables.tf"
    - "particle-flat-observatory/terraform/outputs.tf"
    - "particle-flat-observatory/terraform/iam.tf"
    - "particle-flat-observatory/terraform/terraform.tfvars.example"
    - "particle-flat-observatory/terraform/.gitignore"
  modified: []

key-decisions:
  - "for_each with locals map over 21 separate resource blocks -- DRY, single pattern"
  - "All columns STRING/NULLABLE via jsonencode -- matches existing DDL ELT approach"
  - "5 empty tables created with patient_id placeholder -- tables exist when data arrives"
  - "deletion_protection = false for accelerator context with comment for production"
  - "delete_contents_on_destroy = true for clean terraform destroy"
  - "dataEditor at dataset level, jobUser at project level -- minimum privilege"

patterns-established:
  - "Terraform for_each + locals map: single resource block creates N tables from a map"
  - "IAM scoping: dataset-level for data access, project-level for job execution"
  - "Accelerator defaults: destructive operations enabled with production guidance in comments"

# Metrics
duration: 2min
completed: 2026-02-08
---

# Phase 4 Plan 1: Terraform BigQuery Infrastructure Summary

**Terraform HCL module provisioning BigQuery dataset, 21 resource type tables via for_each, and service account with minimum IAM (dataEditor + jobUser)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-08T15:21:37Z
- **Completed:** 2026-02-08T15:23:47Z
- **Tasks:** 2
- **Files created:** 6

## Accomplishments
- Complete Terraform module that provisions entire BigQuery infrastructure with `terraform apply`
- All 21 Particle resource type tables with exact column schemas from DDL (16 data + 5 empty)
- Service account with minimum permissions: dataEditor (dataset-scoped) + jobUser (project-scoped)
- All configuration driven by variables with sensible defaults (project_id required, dataset_name and region have defaults)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Terraform module with dataset, tables, and variables** - `f2ebe22` (feat)
2. **Task 2: Create IAM resources for service account** - `56eae57` (feat)

## Files Created/Modified
- `particle-flat-observatory/terraform/main.tf` - Provider config, BigQuery dataset, locals with 21 table schemas, google_bigquery_table for_each resource
- `particle-flat-observatory/terraform/variables.tf` - Customer-configurable project_id, dataset_name, region
- `particle-flat-observatory/terraform/outputs.tf` - dataset_id, dataset_location, service_account_email, table_count
- `particle-flat-observatory/terraform/iam.tf` - Service account + dataEditor (dataset) + jobUser (project) IAM bindings
- `particle-flat-observatory/terraform/terraform.tfvars.example` - Example variable values for customer
- `particle-flat-observatory/terraform/.gitignore` - Excludes .terraform/, tfstate, tfvars (not example)

## Decisions Made
- Used `for_each` with a locals map instead of 21 separate resource blocks. Single pattern is DRY and maintainable.
- All columns defined as STRING/NULLABLE via `jsonencode`, matching the existing DDL's ELT approach (transform in queries, not on load).
- 5 empty tables (allergies, coverages, family_member_histories, immunizations, social_histories) created with `patient_id` placeholder column so tables exist when data becomes available.
- `deletion_protection = false` and `delete_contents_on_destroy = true` for accelerator context, with comments noting production should change these.
- Service account uses minimum privilege: `dataEditor` scoped to dataset (read/write data), `jobUser` scoped to project (BigQuery cannot scope job permissions to a dataset).

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

Terraform CLI not available in environment, so `terraform fmt -check` and `terraform validate` could not be run. Verified correctness by:
- Automated Python script comparing all 21 table names and column counts against DDL source of truth
- Manual inspection of HCL syntax against provider documentation patterns
- Grep-based verification of resource counts, variable references, and IAM bindings

## User Setup Required

None -- no external service configuration required. Customers will need to:
1. Install Terraform >= 1.0
2. Copy `terraform.tfvars.example` to `terraform.tfvars` and set their GCP project ID
3. Run `terraform init && terraform apply`

## Next Phase Readiness
- BigQuery dataset and table infrastructure ready for Plan 02 (Python BigQuery loader module)
- Service account and IAM bindings ready for pipeline authentication
- Table schemas in Terraform locals mirror DDL exactly, ensuring loader column lists will match

---
*Phase: 04-cloud-mode*
*Completed: 2026-02-08*
