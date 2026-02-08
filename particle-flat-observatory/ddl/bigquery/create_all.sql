-- Particle Flat Data Observatory
-- DDL for bigquery — Generated from sample data
-- All columns are STRING (ELT approach: transform in queries, not on load)
--
-- Resource types: 21 total, 16 with data, 5 empty
-- Generated: 2026-02-08T05:40:35Z

-- ai_citations: 542 records, 7 columns
CREATE TABLE IF NOT EXISTS ai_citations (
  `ai_output_id` STRING,
  `citation_id` STRING,
  `particle_patient_id` STRING,
  `patient_id` STRING,
  `resource_reference_id` STRING,
  `resource_type` STRING,
  `text_snippet` STRING
);

-- ai_outputs: 22 records, 6 columns
CREATE TABLE IF NOT EXISTS ai_outputs (
  `ai_output_id` STRING,
  `created` STRING,
  `patient_id` STRING,
  `resource_reference_ids` STRING,
  `text` STRING,
  `type` STRING
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
  `document_reference_content_data` STRING,
  `document_reference_content_type` STRING,
  `document_reference_id` STRING,
  `document_reference_type` STRING,
  `document_reference_type_code` STRING,
  `document_reference_type_coding_system` STRING,
  `encounter_reference_id` STRING,
  `patient_id` STRING,
  `practitioner_role_reference_id` STRING,
  `subject_patient_id` STRING
);

-- encounters: 5 records, 13 columns
CREATE TABLE IF NOT EXISTS encounters (
  `condition_id_references` STRING,
  `encounter_end_time` STRING,
  `encounter_id` STRING,
  `encounter_start_time` STRING,
  `encounter_text` STRING,
  `encounter_type_code` STRING,
  `encounter_type_code_system` STRING,
  `encounter_type_name` STRING,
  `hospitalization_discharge_disposition` STRING,
  `location_id_references` STRING,
  `patient_id` STRING,
  `practitioner_role_id_references` STRING,
  `subject_patient_id` STRING
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
  `diagnostic_interpreter_practitioner_role_reference_id` STRING,
  `diagnostic_performer_practitioner_role_reference_id` STRING,
  `diagnostic_report_id` STRING,
  `diagnostic_report_name` STRING,
  `lab_code` STRING,
  `lab_code_system` STRING,
  `lab_interpretation` STRING,
  `lab_name` STRING,
  `lab_observation_id` STRING,
  `lab_text` STRING,
  `lab_timestamp` STRING,
  `lab_unit` STRING,
  `lab_unit_quantity` STRING,
  `lab_value` STRING,
  `lab_value_boolean` STRING,
  `lab_value_code` STRING,
  `lab_value_code_system` STRING,
  `lab_value_quantity` STRING,
  `lab_value_string` STRING,
  `observation_category` STRING,
  `patient_id` STRING,
  `subject_patient_id` STRING
);

-- locations: 1 records, 11 columns
CREATE TABLE IF NOT EXISTS locations (
  `location_address` STRING,
  `location_address_use` STRING,
  `location_city` STRING,
  `location_id` STRING,
  `location_name` STRING,
  `location_postal_code` STRING,
  `location_state` STRING,
  `location_type` STRING,
  `location_type_code` STRING,
  `location_type_code_system` STRING,
  `patient_id` STRING
);

-- medications: 6 records, 18 columns
CREATE TABLE IF NOT EXISTS medications (
  `medication_code` STRING,
  `medication_code_system` STRING,
  `medication_id` STRING,
  `medication_name` STRING,
  `medication_reference` STRING,
  `medication_resource_type` STRING,
  `medication_statement_dose_route` STRING,
  `medication_statement_dose_unit` STRING,
  `medication_statement_dose_value` STRING,
  `medication_statement_end_time` STRING,
  `medication_statement_id` STRING,
  `medication_statement_patient_instructions` STRING,
  `medication_statement_start_time` STRING,
  `medication_statement_status` STRING,
  `medication_statement_text` STRING,
  `patient_id` STRING,
  `practitioner_role_id` STRING,
  `subject_patient_id` STRING
);

-- organizations: 4 records, 12 columns
CREATE TABLE IF NOT EXISTS organizations (
  `organization_address_city` STRING,
  `organization_address_country` STRING,
  `organization_address_lines` STRING,
  `organization_address_postal_code` STRING,
  `organization_address_state` STRING,
  `organization_address_use` STRING,
  `organization_id` STRING,
  `organization_name` STRING,
  `organization_telecom_system` STRING,
  `organization_telecom_use` STRING,
  `organization_telecom_value` STRING,
  `patient_id` STRING
);

-- patients: 1 records, 15 columns
CREATE TABLE IF NOT EXISTS patients (
  `address_city` STRING,
  `address_county` STRING,
  `address_line` STRING,
  `address_postal_code` STRING,
  `address_state` STRING,
  `date_of_birth` STRING,
  `family_name` STRING,
  `gender` STRING,
  `given_name` STRING,
  `language` STRING,
  `marital_status` STRING,
  `patient_id` STRING,
  `race` STRING,
  `resource_id` STRING,
  `telephone` STRING
);

-- practitioners: 4 records, 20 columns
CREATE TABLE IF NOT EXISTS practitioners (
  `patient_id` STRING,
  `practitioner_address_city` STRING,
  `practitioner_address_state` STRING,
  `practitioner_address_street` STRING,
  `practitioner_address_use` STRING,
  `practitioner_family_name` STRING,
  `practitioner_given_name` STRING,
  `practitioner_id` STRING,
  `practitioner_identifier_system` STRING,
  `practitioner_identifier_value` STRING,
  `practitioner_name_suffix` STRING,
  `practitioner_role` STRING,
  `practitioner_role_code` STRING,
  `practitioner_role_code_system` STRING,
  `practitioner_role_id` STRING,
  `practitioner_role_specialty` STRING,
  `practitioner_role_specialty_code` STRING,
  `practitioner_role_specialty_code_system` STRING,
  `practitioner_telecom_system` STRING,
  `practitioner_telecom_value` STRING
);

-- problems: 5 records, 14 columns
CREATE TABLE IF NOT EXISTS problems (
  `condition_category_code` STRING,
  `condition_category_code_name` STRING,
  `condition_category_code_system` STRING,
  `condition_clinical_status` STRING,
  `condition_code` STRING,
  `condition_code_system` STRING,
  `condition_id` STRING,
  `condition_name` STRING,
  `condition_onset_date` STRING,
  `condition_recorded_date` STRING,
  `condition_text` STRING,
  `encounter_id` STRING,
  `patient_id` STRING,
  `subject_patient_id` STRING
);

-- procedures: 4 records, 14 columns
CREATE TABLE IF NOT EXISTS procedures (
  `asserter_practitioner_role_reference_id` STRING,
  `encounter_reference_id` STRING,
  `patient_id` STRING,
  `performer_practitioner_role_reference_id` STRING,
  `procedure_code` STRING,
  `procedure_code_system` STRING,
  `procedure_date_time` STRING,
  `procedure_id` STRING,
  `procedure_name` STRING,
  `procedure_reason` STRING,
  `procedure_reason_code` STRING,
  `procedure_reason_code_system` STRING,
  `procedure_text` STRING,
  `subject_patient_id` STRING
);

-- record_sources: 307 records, 5 columns
CREATE TABLE IF NOT EXISTS record_sources (
  `patient_id` STRING,
  `resource_id` STRING,
  `resource_id_name` STRING,
  `resource_type` STRING,
  `source_id` STRING
);

-- Table: social_histories
-- No records found in sample data. Columns unknown.
-- Add columns manually when data becomes available.
-- CREATE TABLE social_histories ();

-- sources: 6 records, 3 columns
CREATE TABLE IF NOT EXISTS sources (
  `patient_id` STRING,
  `source_id` STRING,
  `source_name` STRING
);

-- transitions: 2 records, 36 columns
CREATE TABLE IF NOT EXISTS transitions (
  `address` STRING,
  `admitting_diagnosis_code` STRING,
  `admitting_diagnosis_code_system` STRING,
  `admitting_diagnosis_code_system_name` STRING,
  `admitting_diagnosis_description` STRING,
  `attending_physician_name` STRING,
  `attending_physician_npi` STRING,
  `city` STRING,
  `discharge_diagnosis_code` STRING,
  `discharge_diagnosis_code_system` STRING,
  `discharge_diagnosis_code_system_name` STRING,
  `discharge_diagnosis_description` STRING,
  `discharge_disposition` STRING,
  `discharge_summary` STRING,
  `dob` STRING,
  `facility_name` STRING,
  `facility_npi` STRING,
  `facility_type` STRING,
  `first_name` STRING,
  `gender` STRING,
  `last_name` STRING,
  `particle_patient_id` STRING,
  `patient_id` STRING,
  `phone_number` STRING,
  `setting` STRING,
  `state` STRING,
  `status` STRING,
  `status_date_time` STRING,
  `transition_id` STRING,
  `visit_diagnosis_reference_ids` STRING,
  `visit_encounter_reference_ids` STRING,
  `visit_end_date_time` STRING,
  `visit_id` STRING,
  `visit_medication_reference_ids` STRING,
  `visit_start_date_time` STRING,
  `zip` STRING
);

-- vital_signs: 116 records, 12 columns
CREATE TABLE IF NOT EXISTS vital_signs (
  `observation_category` STRING,
  `patient_id` STRING,
  `subject_patient_id` STRING,
  `vital_sign_grouping_observation_id` STRING,
  `vital_sign_observation_code` STRING,
  `vital_sign_observation_code_system` STRING,
  `vital_sign_observation_id` STRING,
  `vital_sign_observation_name` STRING,
  `vital_sign_observation_text` STRING,
  `vital_sign_observation_time` STRING,
  `vital_sign_observation_unit` STRING,
  `vital_sign_observation_value` STRING
);
