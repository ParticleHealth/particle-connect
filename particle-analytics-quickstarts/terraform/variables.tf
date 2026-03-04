variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "dataset_name" {
  description = "BigQuery dataset name"
  type        = string
  default     = "particle_observatory"
}

variable "region" {
  description = "BigQuery dataset location (multi-region US/EU or single-region e.g. us-central1)"
  type        = string
  default     = "US"
}

variable "create_service_account" {
  description = "Create a dedicated service account for the pipeline. Set to false when using ADC or if you lack IAM permissions."
  type        = bool
  default     = false
}
