output "dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.observatory.dataset_id
}

output "dataset_location" {
  description = "BigQuery dataset location"
  value       = google_bigquery_dataset.observatory.location
}

output "service_account_email" {
  description = "Service account email for pipeline authentication"
  value       = var.create_service_account ? google_service_account.observatory[0].email : "(not created)"
}

output "table_count" {
  description = "Number of BigQuery tables created"
  value       = length(google_bigquery_table.tables)
}
