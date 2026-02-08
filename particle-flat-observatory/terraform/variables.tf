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
  description = "GCP region for dataset location"
  type        = string
  default     = "US"
}
