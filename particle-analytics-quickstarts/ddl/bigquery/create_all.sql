-- Particle Flat Data Observatory
-- DDL for bigquery — Generated from sample data
-- All columns are STRING (ELT approach: transform in queries, not on load)
--
-- Resource types: 22 total, 16 with data, 6 empty in sample data
-- Generated: 2026-02-08T05:40:35Z
-- Columns not present in sample data were added from the FLAT data contract

-- ai_citations: 542 records, 7 columns
CREATE TABLE IF NOT EXISTS ai_citations (
  `ai_output_id` STRING,
  `citation_id` STRING,
  `particle_patient_id` STRING,
  `preferred_document_reference_id` STRING,
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

-- allergies: 0 records, 21 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS allergies (
  `allergy_code` STRING,
  `allergy_code_rxnorm` STRING,
  `allergy_code_rxnorm_name` STRING,
  `allergy_code_snomed` STRING,
  `allergy_code_snomed_name` STRING,
  `allergy_code_system` STRING,
  `allergy_id` STRING,
  `allergy_name` STRING,
  `allergy_onset_end` STRING,
  `allergy_onset_start` STRING,
  `patient_id` STRING,
  `practitioner_role_id` STRING,
  `reaction_manifestation` STRING,
  `reaction_manifestation_code` STRING,
  `reaction_manifestation_code_icd10` STRING,
  `reaction_manifestation_code_icd10_name` STRING,
  `reaction_manifestation_code_snomed` STRING,
  `reaction_manifestation_code_snomed_name` STRING,
  `reaction_manifestation_code_system` STRING,
  `recorded_date` STRING,
  `subject_patient_id` STRING
);

-- coverages: 0 records, 20 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS coverages (
  `beneficiary_reference` STRING,
  `class_type_code` STRING,
  `class_type_code_system` STRING,
  `class_type_display` STRING,
  `class_value` STRING,
  `coverage_id` STRING,
  `identifier_system` STRING,
  `identifier_value` STRING,
  `order` STRING,
  `patient_id` STRING,
  `payor_reference` STRING,
  `relationship_code` STRING,
  `relationship_code_system` STRING,
  `relationship_display` STRING,
  `status` STRING,
  `subscriber_id` STRING,
  `subscriber_reference` STRING,
  `type_code` STRING,
  `type_code_system` STRING,
  `type_display` STRING
);

-- document_references: 51 records, 13 columns
CREATE TABLE IF NOT EXISTS document_references (
  `document_reference_content_data` STRING,
  `document_reference_content_type` STRING,
  `document_reference_id` STRING,
  `document_reference_type` STRING,
  `document_reference_type_code` STRING,
  `document_reference_type_code_snomed` STRING,
  `document_reference_type_code_snomed_name` STRING,
  `document_reference_type_coding_system` STRING,
  `encounter_reference_id` STRING,
  `last_updated` STRING,
  `patient_id` STRING,
  `practitioner_role_reference_id` STRING,
  `subject_patient_id` STRING
);

-- encounters: 5 records, 19 columns
CREATE TABLE IF NOT EXISTS encounters (
  `condition_id_references` STRING,
  `encounter_end_time` STRING,
  `encounter_id` STRING,
  `encounter_start_time` STRING,
  `encounter_text` STRING,
  `encounter_type_code` STRING,
  `encounter_type_code_cpt` STRING,
  `encounter_type_code_cpt_name` STRING,
  `encounter_type_code_icd10` STRING,
  `encounter_type_code_icd10_name` STRING,
  `encounter_type_code_snomed` STRING,
  `encounter_type_code_snomed_name` STRING,
  `encounter_type_code_system` STRING,
  `encounter_type_name` STRING,
  `hospitalization_discharge_disposition` STRING,
  `location_id_references` STRING,
  `patient_id` STRING,
  `practitioner_role_id_references` STRING,
  `subject_patient_id` STRING
);

-- family_member_histories: 0 records, 11 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS family_member_histories (
  `family_member_history_condition_code` STRING,
  `family_member_history_condition_code_system` STRING,
  `family_member_history_condition_display` STRING,
  `family_member_history_id` STRING,
  `family_member_history_relationship_code` STRING,
  `family_member_history_relationship_code_system` STRING,
  `family_member_history_relationship_display` STRING,
  `family_member_history_sex_code` STRING,
  `family_member_history_sex_code_system` STRING,
  `family_member_history_sex_display` STRING,
  `patient_id` STRING
);

-- immunizations: 0 records, 27 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS immunizations (
  `immunization_code` STRING,
  `immunization_code_cvx` STRING,
  `immunization_code_cvx_name` STRING,
  `immunization_code_ndc` STRING,
  `immunization_code_ndc_name` STRING,
  `immunization_code_rxnorm` STRING,
  `immunization_code_rxnorm_name` STRING,
  `immunization_code_snomed` STRING,
  `immunization_code_snomed_name` STRING,
  `immunization_code_system` STRING,
  `immunization_dosage_unit` STRING,
  `immunization_dosage_value` STRING,
  `immunization_id` STRING,
  `immunization_lot_number` STRING,
  `immunization_manufacturer_name` STRING,
  `immunization_name` STRING,
  `immunization_occurrence_time` STRING,
  `immunization_route` STRING,
  `immunization_route_code` STRING,
  `immunization_route_code_system` STRING,
  `immunization_site` STRING,
  `immunization_site_code` STRING,
  `immunization_site_code_system` STRING,
  `immunization_status` STRING,
  `patient_id` STRING,
  `performer_practitioner_role_reference_id` STRING,
  `subject_patient_id` STRING
);

-- labs: 111 records, 42 columns
CREATE TABLE IF NOT EXISTS labs (
  `diagnostic_interpreter_practitioner_role_reference_id` STRING,
  `diagnostic_performer_practitioner_role_reference_id` STRING,
  `diagnostic_report_code` STRING,
  `diagnostic_report_code_cpt` STRING,
  `diagnostic_report_code_cpt_name` STRING,
  `diagnostic_report_code_loinc` STRING,
  `diagnostic_report_code_loinc_name` STRING,
  `diagnostic_report_code_snomed` STRING,
  `diagnostic_report_code_snomed_name` STRING,
  `diagnostic_report_code_system` STRING,
  `diagnostic_report_id` STRING,
  `diagnostic_report_name` STRING,
  `lab_code` STRING,
  `lab_code_cpt` STRING,
  `lab_code_cpt_name` STRING,
  `lab_code_loinc` STRING,
  `lab_code_loinc_name` STRING,
  `lab_code_snomed` STRING,
  `lab_code_snomed_name` STRING,
  `lab_code_system` STRING,
  `lab_interpretation` STRING,
  `lab_name` STRING,
  `lab_observation_id` STRING,
  `lab_reference_range_high` STRING,
  `lab_reference_range_interpretation` STRING,
  `lab_reference_range_interpretation_code` STRING,
  `lab_reference_range_low` STRING,
  `lab_reference_range_text` STRING,
  `lab_reference_range_unit` STRING,
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

-- medication_fills: 0 records, 35 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS medication_fills (
  `code_list_qualifier` STRING,
  `days_supply` STRING,
  `dea_schedule` STRING,
  `directions` STRING,
  `electronic_prescription` STRING,
  `history_source_fill_number` STRING,
  `last_filled_date` STRING,
  `medication_id` STRING,
  `medication_name` STRING,
  `medication_statement_start_time` STRING,
  `ndc_code` STRING,
  `patient_id` STRING,
  `pharmacy_city` STRING,
  `pharmacy_ncpdp_id` STRING,
  `pharmacy_npi` STRING,
  `pharmacy_state` STRING,
  `pharmacy_store_name` STRING,
  `prescriber_name` STRING,
  `prescriber_npi` STRING,
  `prescription_number` STRING,
  `product_code` STRING,
  `quantity_prescribed` STRING,
  `quantity_unit_code` STRING,
  `record_id` STRING,
  `refills_qualifier` STRING,
  `refills_value` STRING,
  `rxcui` STRING,
  `sent_time` STRING,
  `sold_date` STRING,
  `strength` STRING,
  `strength_code` STRING,
  `strength_source_code` STRING,
  `substitutions` STRING,
  `unit_source_code` STRING,
  `written_date` STRING
);

-- medications: 6 records, 25 columns
CREATE TABLE IF NOT EXISTS medications (
  `medication_code` STRING,
  `medication_code_ndc` STRING,
  `medication_code_ndc_name` STRING,
  `medication_code_rxnorm` STRING,
  `medication_code_rxnorm_name` STRING,
  `medication_code_snomed` STRING,
  `medication_code_snomed_name` STRING,
  `medication_code_system` STRING,
  `medication_context` STRING,
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

-- problems: 5 records, 18 columns
CREATE TABLE IF NOT EXISTS problems (
  `condition_category_code` STRING,
  `condition_category_code_name` STRING,
  `condition_category_code_system` STRING,
  `condition_clinical_status` STRING,
  `condition_code` STRING,
  `condition_code_icd10` STRING,
  `condition_code_icd10_name` STRING,
  `condition_code_snomed` STRING,
  `condition_code_snomed_name` STRING,
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

-- procedures: 4 records, 22 columns
CREATE TABLE IF NOT EXISTS procedures (
  `asserter_practitioner_role_reference_id` STRING,
  `encounter_reference_id` STRING,
  `patient_id` STRING,
  `performer_practitioner_role_reference_id` STRING,
  `procedure_code` STRING,
  `procedure_code_cpt` STRING,
  `procedure_code_cpt_name` STRING,
  `procedure_code_snomed` STRING,
  `procedure_code_snomed_name` STRING,
  `procedure_code_system` STRING,
  `procedure_date_time` STRING,
  `procedure_id` STRING,
  `procedure_name` STRING,
  `procedure_reason` STRING,
  `procedure_reason_code` STRING,
  `procedure_reason_code_icd10` STRING,
  `procedure_reason_code_icd10_name` STRING,
  `procedure_reason_code_snomed` STRING,
  `procedure_reason_code_snomed_name` STRING,
  `procedure_reason_code_system` STRING,
  `procedure_text` STRING,
  `subject_patient_id` STRING
);

-- record_sources: 307 records, 6 columns
CREATE TABLE IF NOT EXISTS record_sources (
  `document_reference_id` STRING,
  `patient_id` STRING,
  `resource_id` STRING,
  `resource_id_name` STRING,
  `resource_type` STRING,
  `source_id` STRING
);

-- social_histories: 0 records, 17 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS social_histories (
  `observation_category` STRING,
  `patient_id` STRING,
  `practitioner_role_reference_id` STRING,
  `social_history_observation_code` STRING,
  `social_history_observation_code_loinc` STRING,
  `social_history_observation_code_loinc_name` STRING,
  `social_history_observation_code_snomed` STRING,
  `social_history_observation_code_snomed_name` STRING,
  `social_history_observation_code_system` STRING,
  `social_history_observation_id` STRING,
  `social_history_observation_name` STRING,
  `social_history_observation_timestamp` STRING,
  `social_history_observation_value` STRING,
  `social_history_observation_value_code` STRING,
  `social_history_observation_value_code_system` STRING,
  `social_history_text` STRING,
  `subject_patient_id` STRING
);

-- sources: 6 records, 12 columns
CREATE TABLE IF NOT EXISTS sources (
  `author_name` STRING,
  `class_code` STRING,
  `event_code` STRING,
  `healthcare_facility_type_code` STRING,
  `patient_id` STRING,
  `practice_setting_code` STRING,
  `service_end_time` STRING,
  `service_start_time` STRING,
  `source_id` STRING,
  `source_name` STRING,
  `title` STRING,
  `type` STRING
);

-- transitions: 2 records, 38 columns
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
  `discharge_disposition_code_hl7` STRING,
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
  `possible_observation_stays` STRING,
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

-- vital_signs: 116 records, 16 columns
CREATE TABLE IF NOT EXISTS vital_signs (
  `observation_category` STRING,
  `patient_id` STRING,
  `subject_patient_id` STRING,
  `vital_sign_grouping_observation_id` STRING,
  `vital_sign_observation_code` STRING,
  `vital_sign_observation_code_loinc` STRING,
  `vital_sign_observation_code_loinc_name` STRING,
  `vital_sign_observation_code_snomed` STRING,
  `vital_sign_observation_code_snomed_name` STRING,
  `vital_sign_observation_code_system` STRING,
  `vital_sign_observation_id` STRING,
  `vital_sign_observation_name` STRING,
  `vital_sign_observation_text` STRING,
  `vital_sign_observation_time` STRING,
  `vital_sign_observation_unit` STRING,
  `vital_sign_observation_value` STRING
);
