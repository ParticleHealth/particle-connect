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
# Derived from ddl/bigquery/create_all.sql -- 22 resource types total.
# Columns not present in sample data come from the FLAT data contract.
# All columns are STRING (ELT approach: transform in queries, not on load).
# -----------------------------------------------------------------------------

locals {
  tables = {
    "ai_citations" = [
      "ai_output_id",
      "citation_id",
      "particle_patient_id",
      "preferred_document_reference_id",
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

    "allergies" = [
      "allergy_code",
      "allergy_code_rxnorm",
      "allergy_code_rxnorm_name",
      "allergy_code_snomed",
      "allergy_code_snomed_name",
      "allergy_code_system",
      "allergy_id",
      "allergy_name",
      "allergy_onset_end",
      "allergy_onset_start",
      "patient_id",
      "practitioner_role_id",
      "reaction_manifestation",
      "reaction_manifestation_code",
      "reaction_manifestation_code_icd10",
      "reaction_manifestation_code_icd10_name",
      "reaction_manifestation_code_snomed",
      "reaction_manifestation_code_snomed_name",
      "reaction_manifestation_code_system",
      "recorded_date",
      "subject_patient_id",
    ]

    "coverages" = [
      "beneficiary_reference",
      "class_type_code",
      "class_type_code_system",
      "class_type_display",
      "class_value",
      "coverage_id",
      "identifier_system",
      "identifier_value",
      "order",
      "patient_id",
      "payor_reference",
      "relationship_code",
      "relationship_code_system",
      "relationship_display",
      "status",
      "subscriber_id",
      "subscriber_reference",
      "type_code",
      "type_code_system",
      "type_display",
    ]

    "document_references" = [
      "document_reference_content_data",
      "document_reference_content_type",
      "document_reference_id",
      "document_reference_type",
      "document_reference_type_code",
      "document_reference_type_code_snomed",
      "document_reference_type_code_snomed_name",
      "document_reference_type_coding_system",
      "encounter_reference_id",
      "last_updated",
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
      "encounter_type_code_cpt",
      "encounter_type_code_cpt_name",
      "encounter_type_code_icd10",
      "encounter_type_code_icd10_name",
      "encounter_type_code_snomed",
      "encounter_type_code_snomed_name",
      "encounter_type_code_system",
      "encounter_type_name",
      "hospitalization_discharge_disposition",
      "location_id_references",
      "patient_id",
      "practitioner_role_id_references",
      "subject_patient_id",
    ]

    "family_member_histories" = [
      "family_member_history_condition_code",
      "family_member_history_condition_code_system",
      "family_member_history_condition_display",
      "family_member_history_id",
      "family_member_history_relationship_code",
      "family_member_history_relationship_code_system",
      "family_member_history_relationship_display",
      "family_member_history_sex_code",
      "family_member_history_sex_code_system",
      "family_member_history_sex_display",
      "patient_id",
    ]

    "immunizations" = [
      "immunization_code",
      "immunization_code_cvx",
      "immunization_code_cvx_name",
      "immunization_code_ndc",
      "immunization_code_ndc_name",
      "immunization_code_rxnorm",
      "immunization_code_rxnorm_name",
      "immunization_code_snomed",
      "immunization_code_snomed_name",
      "immunization_code_system",
      "immunization_dosage_unit",
      "immunization_dosage_value",
      "immunization_id",
      "immunization_lot_number",
      "immunization_manufacturer_name",
      "immunization_name",
      "immunization_occurrence_time",
      "immunization_route",
      "immunization_route_code",
      "immunization_route_code_system",
      "immunization_site",
      "immunization_site_code",
      "immunization_site_code_system",
      "immunization_status",
      "patient_id",
      "performer_practitioner_role_reference_id",
      "subject_patient_id",
    ]

    "labs" = [
      "diagnostic_interpreter_practitioner_role_reference_id",
      "diagnostic_performer_practitioner_role_reference_id",
      "diagnostic_report_code",
      "diagnostic_report_code_cpt",
      "diagnostic_report_code_cpt_name",
      "diagnostic_report_code_loinc",
      "diagnostic_report_code_loinc_name",
      "diagnostic_report_code_snomed",
      "diagnostic_report_code_snomed_name",
      "diagnostic_report_code_system",
      "diagnostic_report_id",
      "diagnostic_report_name",
      "lab_code",
      "lab_code_cpt",
      "lab_code_cpt_name",
      "lab_code_loinc",
      "lab_code_loinc_name",
      "lab_code_snomed",
      "lab_code_snomed_name",
      "lab_code_system",
      "lab_interpretation",
      "lab_name",
      "lab_observation_id",
      "lab_reference_range_high",
      "lab_reference_range_interpretation",
      "lab_reference_range_interpretation_code",
      "lab_reference_range_low",
      "lab_reference_range_text",
      "lab_reference_range_unit",
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

    "medication_fills" = [
      "code_list_qualifier",
      "days_supply",
      "dea_schedule",
      "directions",
      "electronic_prescription",
      "history_source_fill_number",
      "last_filled_date",
      "medication_id",
      "medication_name",
      "medication_statement_start_time",
      "ndc_code",
      "patient_id",
      "pharmacy_city",
      "pharmacy_ncpdp_id",
      "pharmacy_npi",
      "pharmacy_state",
      "pharmacy_store_name",
      "prescriber_name",
      "prescriber_npi",
      "prescription_number",
      "product_code",
      "quantity_prescribed",
      "quantity_unit_code",
      "record_id",
      "refills_qualifier",
      "refills_value",
      "rxcui",
      "sent_time",
      "sold_date",
      "strength",
      "strength_code",
      "strength_source_code",
      "substitutions",
      "unit_source_code",
      "written_date",
    ]

    "medications" = [
      "medication_code",
      "medication_code_ndc",
      "medication_code_ndc_name",
      "medication_code_rxnorm",
      "medication_code_rxnorm_name",
      "medication_code_snomed",
      "medication_code_snomed_name",
      "medication_code_system",
      "medication_context",
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
      "condition_code_icd10",
      "condition_code_icd10_name",
      "condition_code_snomed",
      "condition_code_snomed_name",
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
      "procedure_code_cpt",
      "procedure_code_cpt_name",
      "procedure_code_snomed",
      "procedure_code_snomed_name",
      "procedure_code_system",
      "procedure_date_time",
      "procedure_id",
      "procedure_name",
      "procedure_reason",
      "procedure_reason_code",
      "procedure_reason_code_icd10",
      "procedure_reason_code_icd10_name",
      "procedure_reason_code_snomed",
      "procedure_reason_code_snomed_name",
      "procedure_reason_code_system",
      "procedure_text",
      "subject_patient_id",
    ]

    "record_sources" = [
      "document_reference_id",
      "patient_id",
      "resource_id",
      "resource_id_name",
      "resource_type",
      "source_id",
    ]

    "social_histories" = [
      "observation_category",
      "patient_id",
      "practitioner_role_reference_id",
      "social_history_observation_code",
      "social_history_observation_code_loinc",
      "social_history_observation_code_loinc_name",
      "social_history_observation_code_snomed",
      "social_history_observation_code_snomed_name",
      "social_history_observation_code_system",
      "social_history_observation_id",
      "social_history_observation_name",
      "social_history_observation_timestamp",
      "social_history_observation_value",
      "social_history_observation_value_code",
      "social_history_observation_value_code_system",
      "social_history_text",
      "subject_patient_id",
    ]

    "sources" = [
      "author_name",
      "class_code",
      "event_code",
      "healthcare_facility_type_code",
      "patient_id",
      "practice_setting_code",
      "service_end_time",
      "service_start_time",
      "source_id",
      "source_name",
      "title",
      "type",
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
      "discharge_disposition_code_hl7",
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
      "possible_observation_stays",
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
      "vital_sign_observation_code_loinc",
      "vital_sign_observation_code_loinc_name",
      "vital_sign_observation_code_snomed",
      "vital_sign_observation_code_snomed_name",
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
# All 22 resource type tables created via for_each.
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
