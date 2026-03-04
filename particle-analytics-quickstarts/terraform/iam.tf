# -----------------------------------------------------------------------------
# Service Account and IAM Bindings (optional)
#
# Creates a dedicated service account for production use. Set
# create_service_account = false to skip (e.g. when using ADC with your
# own user account, or when you lack iam.serviceAccounts.create permission).
#
# Minimum permissions for the observatory data pipeline:
#
# - roles/bigquery.dataEditor (dataset-level):
#   Read and write data in tables. Required for DELETE (per-patient cleanup)
#   and INSERT (load job) operations during idempotent data loading.
#
# - roles/bigquery.jobUser (project-level):
#   Create and run BigQuery jobs (load jobs and queries). This role cannot
#   be scoped to a dataset -- it must be granted at the project level.
# -----------------------------------------------------------------------------

resource "google_service_account" "observatory" {
  count        = var.create_service_account ? 1 : 0
  account_id   = "observatory-pipeline"
  display_name = "Observatory Pipeline Service Account"
  project      = var.project_id
}

# Dataset-level: read/write data in tables (DELETE + INSERT operations)
resource "google_bigquery_dataset_iam_member" "data_editor" {
  count      = var.create_service_account ? 1 : 0
  dataset_id = google_bigquery_dataset.observatory.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.observatory[0].email}"
}

# Project-level: create load jobs and run queries (cannot be dataset-scoped)
resource "google_project_iam_member" "job_user" {
  count   = var.create_service_account ? 1 : 0
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.observatory[0].email}"
}
