-- Particle Flat Data Observatory
-- DDL for postgres — Generated from sample data
-- All columns are TEXT (ELT approach: transform in queries, not on load)
--
-- Resource types: 21 total, 16 with data, 5 empty
-- Generated: 2026-02-08T05:40:35Z

-- ai_citations: 542 records, 7 columns
CREATE TABLE IF NOT EXISTS ai_citations (
  "ai_output_id" TEXT,
  "citation_id" TEXT,
  "particle_patient_id" TEXT,
  "patient_id" TEXT,
  "resource_reference_id" TEXT,
  "resource_type" TEXT,
  "text_snippet" TEXT
);

-- ai_outputs: 22 records, 6 columns
CREATE TABLE IF NOT EXISTS ai_outputs (
  "ai_output_id" TEXT,
  "created" TEXT,
  "patient_id" TEXT,
  "resource_reference_ids" TEXT,
  "text" TEXT,
  "type" TEXT
);

-- Table: allergies
-- No records found in sample data. Columns unknown.
-- Add columns manually when data becomes available.
-- CREATE TABLE allergies ();

-- Table: coverages
-- No records found in sample data. Columns unknown.
-- Add columns manually when data becomes available.
-- CREATE TABLE coverages ();

-- document_references: 51 records, 10 columns
CREATE TABLE IF NOT EXISTS document_references (
  "document_reference_content_data" TEXT,
  "document_reference_content_type" TEXT,
  "document_reference_id" TEXT,
  "document_reference_type" TEXT,
  "document_reference_type_code" TEXT,
  "document_reference_type_coding_system" TEXT,
  "encounter_reference_id" TEXT,
  "patient_id" TEXT,
  "practitioner_role_reference_id" TEXT,
  "subject_patient_id" TEXT
);

-- encounters: 5 records, 13 columns
CREATE TABLE IF NOT EXISTS encounters (
  "condition_id_references" TEXT,
  "encounter_end_time" TEXT,
  "encounter_id" TEXT,
  "encounter_start_time" TEXT,
  "encounter_text" TEXT,
  "encounter_type_code" TEXT,
  "encounter_type_code_system" TEXT,
  "encounter_type_name" TEXT,
  "hospitalization_discharge_disposition" TEXT,
  "location_id_references" TEXT,
  "patient_id" TEXT,
  "practitioner_role_id_references" TEXT,
  "subject_patient_id" TEXT
);

-- Table: family_member_histories
-- No records found in sample data. Columns unknown.
-- Add columns manually when data becomes available.
-- CREATE TABLE family_member_histories ();

-- Table: immunizations
-- No records found in sample data. Columns unknown.
-- Add columns manually when data becomes available.
-- CREATE TABLE immunizations ();

-- labs: 111 records, 22 columns
CREATE TABLE IF NOT EXISTS labs (
  "diagnostic_interpreter_practitioner_role_reference_id" TEXT,
  "diagnostic_performer_practitioner_role_reference_id" TEXT,
  "diagnostic_report_id" TEXT,
  "diagnostic_report_name" TEXT,
  "lab_code" TEXT,
  "lab_code_system" TEXT,
  "lab_interpretation" TEXT,
  "lab_name" TEXT,
  "lab_observation_id" TEXT,
  "lab_text" TEXT,
  "lab_timestamp" TEXT,
  "lab_unit" TEXT,
  "lab_unit_quantity" TEXT,
  "lab_value" TEXT,
  "lab_value_boolean" TEXT,
  "lab_value_code" TEXT,
  "lab_value_code_system" TEXT,
  "lab_value_quantity" TEXT,
  "lab_value_string" TEXT,
  "observation_category" TEXT,
  "patient_id" TEXT,
  "subject_patient_id" TEXT
);

-- locations: 1 records, 11 columns
CREATE TABLE IF NOT EXISTS locations (
  "location_address" TEXT,
  "location_address_use" TEXT,
  "location_city" TEXT,
  "location_id" TEXT,
  "location_name" TEXT,
  "location_postal_code" TEXT,
  "location_state" TEXT,
  "location_type" TEXT,
  "location_type_code" TEXT,
  "location_type_code_system" TEXT,
  "patient_id" TEXT
);

-- medications: 6 records, 18 columns
CREATE TABLE IF NOT EXISTS medications (
  "medication_code" TEXT,
  "medication_code_system" TEXT,
  "medication_id" TEXT,
  "medication_name" TEXT,
  "medication_reference" TEXT,
  "medication_resource_type" TEXT,
  "medication_statement_dose_route" TEXT,
  "medication_statement_dose_unit" TEXT,
  "medication_statement_dose_value" TEXT,
  "medication_statement_end_time" TEXT,
  "medication_statement_id" TEXT,
  "medication_statement_patient_instructions" TEXT,
  "medication_statement_start_time" TEXT,
  "medication_statement_status" TEXT,
  "medication_statement_text" TEXT,
  "patient_id" TEXT,
  "practitioner_role_id" TEXT,
  "subject_patient_id" TEXT
);

-- organizations: 4 records, 12 columns
CREATE TABLE IF NOT EXISTS organizations (
  "organization_address_city" TEXT,
  "organization_address_country" TEXT,
  "organization_address_lines" TEXT,
  "organization_address_postal_code" TEXT,
  "organization_address_state" TEXT,
  "organization_address_use" TEXT,
  "organization_id" TEXT,
  "organization_name" TEXT,
  "organization_telecom_system" TEXT,
  "organization_telecom_use" TEXT,
  "organization_telecom_value" TEXT,
  "patient_id" TEXT
);

-- patients: 1 records, 15 columns
CREATE TABLE IF NOT EXISTS patients (
  "address_city" TEXT,
  "address_county" TEXT,
  "address_line" TEXT,
  "address_postal_code" TEXT,
  "address_state" TEXT,
  "date_of_birth" TEXT,
  "family_name" TEXT,
  "gender" TEXT,
  "given_name" TEXT,
  "language" TEXT,
  "marital_status" TEXT,
  "patient_id" TEXT,
  "race" TEXT,
  "resource_id" TEXT,
  "telephone" TEXT
);

-- practitioners: 4 records, 20 columns
CREATE TABLE IF NOT EXISTS practitioners (
  "patient_id" TEXT,
  "practitioner_address_city" TEXT,
  "practitioner_address_state" TEXT,
  "practitioner_address_street" TEXT,
  "practitioner_address_use" TEXT,
  "practitioner_family_name" TEXT,
  "practitioner_given_name" TEXT,
  "practitioner_id" TEXT,
  "practitioner_identifier_system" TEXT,
  "practitioner_identifier_value" TEXT,
  "practitioner_name_suffix" TEXT,
  "practitioner_role" TEXT,
  "practitioner_role_code" TEXT,
  "practitioner_role_code_system" TEXT,
  "practitioner_role_id" TEXT,
  "practitioner_role_specialty" TEXT,
  "practitioner_role_specialty_code" TEXT,
  "practitioner_role_specialty_code_system" TEXT,
  "practitioner_telecom_system" TEXT,
  "practitioner_telecom_value" TEXT
);

-- problems: 5 records, 14 columns
CREATE TABLE IF NOT EXISTS problems (
  "condition_category_code" TEXT,
  "condition_category_code_name" TEXT,
  "condition_category_code_system" TEXT,
  "condition_clinical_status" TEXT,
  "condition_code" TEXT,
  "condition_code_system" TEXT,
  "condition_id" TEXT,
  "condition_name" TEXT,
  "condition_onset_date" TEXT,
  "condition_recorded_date" TEXT,
  "condition_text" TEXT,
  "encounter_id" TEXT,
  "patient_id" TEXT,
  "subject_patient_id" TEXT
);

-- procedures: 4 records, 14 columns
CREATE TABLE IF NOT EXISTS procedures (
  "asserter_practitioner_role_reference_id" TEXT,
  "encounter_reference_id" TEXT,
  "patient_id" TEXT,
  "performer_practitioner_role_reference_id" TEXT,
  "procedure_code" TEXT,
  "procedure_code_system" TEXT,
  "procedure_date_time" TEXT,
  "procedure_id" TEXT,
  "procedure_name" TEXT,
  "procedure_reason" TEXT,
  "procedure_reason_code" TEXT,
  "procedure_reason_code_system" TEXT,
  "procedure_text" TEXT,
  "subject_patient_id" TEXT
);

-- record_sources: 307 records, 5 columns
CREATE TABLE IF NOT EXISTS record_sources (
  "patient_id" TEXT,
  "resource_id" TEXT,
  "resource_id_name" TEXT,
  "resource_type" TEXT,
  "source_id" TEXT
);

-- Table: social_histories
-- No records found in sample data. Columns unknown.
-- Add columns manually when data becomes available.
-- CREATE TABLE social_histories ();

-- sources: 6 records, 3 columns
CREATE TABLE IF NOT EXISTS sources (
  "patient_id" TEXT,
  "source_id" TEXT,
  "source_name" TEXT
);

-- transitions: 2 records, 36 columns
CREATE TABLE IF NOT EXISTS transitions (
  "address" TEXT,
  "admitting_diagnosis_code" TEXT,
  "admitting_diagnosis_code_system" TEXT,
  "admitting_diagnosis_code_system_name" TEXT,
  "admitting_diagnosis_description" TEXT,
  "attending_physician_name" TEXT,
  "attending_physician_npi" TEXT,
  "city" TEXT,
  "discharge_diagnosis_code" TEXT,
  "discharge_diagnosis_code_system" TEXT,
  "discharge_diagnosis_code_system_name" TEXT,
  "discharge_diagnosis_description" TEXT,
  "discharge_disposition" TEXT,
  "discharge_summary" TEXT,
  "dob" TEXT,
  "facility_name" TEXT,
  "facility_npi" TEXT,
  "facility_type" TEXT,
  "first_name" TEXT,
  "gender" TEXT,
  "last_name" TEXT,
  "particle_patient_id" TEXT,
  "patient_id" TEXT,
  "phone_number" TEXT,
  "setting" TEXT,
  "state" TEXT,
  "status" TEXT,
  "status_date_time" TEXT,
  "transition_id" TEXT,
  "visit_diagnosis_reference_ids" TEXT,
  "visit_encounter_reference_ids" TEXT,
  "visit_end_date_time" TEXT,
  "visit_id" TEXT,
  "visit_medication_reference_ids" TEXT,
  "visit_start_date_time" TEXT,
  "zip" TEXT
);

-- vital_signs: 116 records, 12 columns
CREATE TABLE IF NOT EXISTS vital_signs (
  "observation_category" TEXT,
  "patient_id" TEXT,
  "subject_patient_id" TEXT,
  "vital_sign_grouping_observation_id" TEXT,
  "vital_sign_observation_code" TEXT,
  "vital_sign_observation_code_system" TEXT,
  "vital_sign_observation_id" TEXT,
  "vital_sign_observation_name" TEXT,
  "vital_sign_observation_text" TEXT,
  "vital_sign_observation_time" TEXT,
  "vital_sign_observation_unit" TEXT,
  "vital_sign_observation_value" TEXT
);
