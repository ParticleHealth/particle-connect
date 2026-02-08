terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# -----------------------------------------------------------------------------
# BigQuery Dataset
# -----------------------------------------------------------------------------

resource "google_bigquery_dataset" "observatory" {
  dataset_id    = var.dataset_name
  project       = var.project_id
  location      = var.region
  friendly_name = "Particle Flat Data Observatory"
  description   = "Structured tables for Particle Health flat data analytics"

  # Allow terraform destroy for accelerator use.
  # Production deployments should remove this or set to false.
  delete_contents_on_destroy = true
}

# -----------------------------------------------------------------------------
# Table Schemas
# Derived from ddl/bigquery/create_all.sql -- 21 resource types total.
# 16 tables with data columns, 5 empty tables with patient_id placeholder.
# All columns are STRING (ELT approach: transform in queries, not on load).
# -----------------------------------------------------------------------------

locals {
  tables = {
    "ai_citations" = [
      "ai_output_id",
      "citation_id",
      "particle_patient_id",
      "patient_id",
      "resource_reference_id",
      "resource_type",
      "text_snippet",
    ]

    "ai_outputs" = [
      "ai_output_id",
      "created",
      "patient_id",
      "resource_reference_ids",
      "text",
      "type",
    ]

    # Empty table -- no sample data. Placeholder column for when data becomes available.
    "allergies" = [
      "patient_id",
    ]

    # Empty table -- no sample data. Placeholder column for when data becomes available.
    "coverages" = [
      "patient_id",
    ]

    "document_references" = [
      "document_reference_content_data",
      "document_reference_content_type",
      "document_reference_id",
      "document_reference_type",
      "document_reference_type_code",
      "document_reference_type_coding_system",
      "encounter_reference_id",
      "patient_id",
      "practitioner_role_reference_id",
      "subject_patient_id",
    ]

    "encounters" = [
      "condition_id_references",
      "encounter_end_time",
      "encounter_id",
      "encounter_start_time",
      "encounter_text",
      "encounter_type_code",
      "encounter_type_code_system",
      "encounter_type_name",
      "hospitalization_discharge_disposition",
      "location_id_references",
      "patient_id",
      "practitioner_role_id_references",
      "subject_patient_id",
    ]

    # Empty table -- no sample data. Placeholder column for when data becomes available.
    "family_member_histories" = [
      "patient_id",
    ]

    # Empty table -- no sample data. Placeholder column for when data becomes available.
    "immunizations" = [
      "patient_id",
    ]

    "labs" = [
      "diagnostic_interpreter_practitioner_role_reference_id",
      "diagnostic_performer_practitioner_role_reference_id",
      "diagnostic_report_id",
      "diagnostic_report_name",
      "lab_code",
      "lab_code_system",
      "lab_interpretation",
      "lab_name",
      "lab_observation_id",
      "lab_text",
      "lab_timestamp",
      "lab_unit",
      "lab_unit_quantity",
      "lab_value",
      "lab_value_boolean",
      "lab_value_code",
      "lab_value_code_system",
      "lab_value_quantity",
      "lab_value_string",
      "observation_category",
      "patient_id",
      "subject_patient_id",
    ]

    "locations" = [
      "location_address",
      "location_address_use",
      "location_city",
      "location_id",
      "location_name",
      "location_postal_code",
      "location_state",
      "location_type",
      "location_type_code",
      "location_type_code_system",
      "patient_id",
    ]

    "medications" = [
      "medication_code",
      "medication_code_system",
      "medication_id",
      "medication_name",
      "medication_reference",
      "medication_resource_type",
      "medication_statement_dose_route",
      "medication_statement_dose_unit",
      "medication_statement_dose_value",
      "medication_statement_end_time",
      "medication_statement_id",
      "medication_statement_patient_instructions",
      "medication_statement_start_time",
      "medication_statement_status",
      "medication_statement_text",
      "patient_id",
      "practitioner_role_id",
      "subject_patient_id",
    ]

    "organizations" = [
      "organization_address_city",
      "organization_address_country",
      "organization_address_lines",
      "organization_address_postal_code",
      "organization_address_state",
      "organization_address_use",
      "organization_id",
      "organization_name",
      "organization_telecom_system",
      "organization_telecom_use",
      "organization_telecom_value",
      "patient_id",
    ]

    "patients" = [
      "address_city",
      "address_county",
      "address_line",
      "address_postal_code",
      "address_state",
      "date_of_birth",
      "family_name",
      "gender",
      "given_name",
      "language",
      "marital_status",
      "patient_id",
      "race",
      "resource_id",
      "telephone",
    ]

    "practitioners" = [
      "patient_id",
      "practitioner_address_city",
      "practitioner_address_state",
      "practitioner_address_street",
      "practitioner_address_use",
      "practitioner_family_name",
      "practitioner_given_name",
      "practitioner_id",
      "practitioner_identifier_system",
      "practitioner_identifier_value",
      "practitioner_name_suffix",
      "practitioner_role",
      "practitioner_role_code",
      "practitioner_role_code_system",
      "practitioner_role_id",
      "practitioner_role_specialty",
      "practitioner_role_specialty_code",
      "practitioner_role_specialty_code_system",
      "practitioner_telecom_system",
      "practitioner_telecom_value",
    ]

    "problems" = [
      "condition_category_code",
      "condition_category_code_name",
      "condition_category_code_system",
      "condition_clinical_status",
      "condition_code",
      "condition_code_system",
      "condition_id",
      "condition_name",
      "condition_onset_date",
      "condition_recorded_date",
      "condition_text",
      "encounter_id",
      "patient_id",
      "subject_patient_id",
    ]

    "procedures" = [
      "asserter_practitioner_role_reference_id",
      "encounter_reference_id",
      "patient_id",
      "performer_practitioner_role_reference_id",
      "procedure_code",
      "procedure_code_system",
      "procedure_date_time",
      "procedure_id",
      "procedure_name",
      "procedure_reason",
      "procedure_reason_code",
      "procedure_reason_code_system",
      "procedure_text",
      "subject_patient_id",
    ]

    "record_sources" = [
      "patient_id",
      "resource_id",
      "resource_id_name",
      "resource_type",
      "source_id",
    ]

    # Empty table -- no sample data. Placeholder column for when data becomes available.
    "social_histories" = [
      "patient_id",
    ]

    "sources" = [
      "patient_id",
      "source_id",
      "source_name",
    ]

    "transitions" = [
      "address",
      "admitting_diagnosis_code",
      "admitting_diagnosis_code_system",
      "admitting_diagnosis_code_system_name",
      "admitting_diagnosis_description",
      "attending_physician_name",
      "attending_physician_npi",
      "city",
      "discharge_diagnosis_code",
      "discharge_diagnosis_code_system",
      "discharge_diagnosis_code_system_name",
      "discharge_diagnosis_description",
      "discharge_disposition",
      "discharge_summary",
      "dob",
      "facility_name",
      "facility_npi",
      "facility_type",
      "first_name",
      "gender",
      "last_name",
      "particle_patient_id",
      "patient_id",
      "phone_number",
      "setting",
      "state",
      "status",
      "status_date_time",
      "transition_id",
      "visit_diagnosis_reference_ids",
      "visit_encounter_reference_ids",
      "visit_end_date_time",
      "visit_id",
      "visit_medication_reference_ids",
      "visit_start_date_time",
      "zip",
    ]

    "vital_signs" = [
      "observation_category",
      "patient_id",
      "subject_patient_id",
      "vital_sign_grouping_observation_id",
      "vital_sign_observation_code",
      "vital_sign_observation_code_system",
      "vital_sign_observation_id",
      "vital_sign_observation_name",
      "vital_sign_observation_text",
      "vital_sign_observation_time",
      "vital_sign_observation_unit",
      "vital_sign_observation_value",
    ]
  }
}

# -----------------------------------------------------------------------------
# BigQuery Tables
# All 21 resource type tables created via for_each.
# All columns are STRING, NULLABLE (ELT approach).
# deletion_protection disabled for accelerator use -- enable in production.
# -----------------------------------------------------------------------------

resource "google_bigquery_table" "tables" {
  for_each   = local.tables
  dataset_id = google_bigquery_dataset.observatory.dataset_id
  project    = var.project_id
  table_id   = each.key

  deletion_protection = false

  schema = jsonencode([
    for col in each.value : {
      name = col
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}
