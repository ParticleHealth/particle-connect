-- Particle Flat Data Observatory
-- DDL for duckdb — Generated from sample data
-- All columns are TEXT (ELT approach: transform in queries, not on load)
--
-- Resource types: 22 total, 16 with data, 6 empty in sample data
-- Generated: 2026-02-11T15:33:49Z
-- Columns not present in sample data were added from the FLAT data contract

-- ai_citations: 542 records, 7 columns
CREATE TABLE IF NOT EXISTS ai_citations (
  "ai_output_id" TEXT,
  "citation_id" TEXT,
  "particle_patient_id" TEXT,
  "preferred_document_reference_id" TEXT,
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

-- allergies: 0 records, 21 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS allergies (
  "allergy_code" TEXT,
  "allergy_code_rxnorm" TEXT,
  "allergy_code_rxnorm_name" TEXT,
  "allergy_code_snomed" TEXT,
  "allergy_code_snomed_name" TEXT,
  "allergy_code_system" TEXT,
  "allergy_id" TEXT,
  "allergy_name" TEXT,
  "allergy_onset_end" TEXT,
  "allergy_onset_start" TEXT,
  "patient_id" TEXT,
  "practitioner_role_id" TEXT,
  "reaction_manifestation" TEXT,
  "reaction_manifestation_code" TEXT,
  "reaction_manifestation_code_icd10" TEXT,
  "reaction_manifestation_code_icd10_name" TEXT,
  "reaction_manifestation_code_snomed" TEXT,
  "reaction_manifestation_code_snomed_name" TEXT,
  "reaction_manifestation_code_system" TEXT,
  "recorded_date" TEXT,
  "subject_patient_id" TEXT
);

-- coverages: 0 records, 20 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS coverages (
  "beneficiary_reference" TEXT,
  "class_type_code" TEXT,
  "class_type_code_system" TEXT,
  "class_type_display" TEXT,
  "class_value" TEXT,
  "coverage_id" TEXT,
  "identifier_system" TEXT,
  "identifier_value" TEXT,
  "order" TEXT,
  "patient_id" TEXT,
  "payor_reference" TEXT,
  "relationship_code" TEXT,
  "relationship_code_system" TEXT,
  "relationship_display" TEXT,
  "status" TEXT,
  "subscriber_id" TEXT,
  "subscriber_reference" TEXT,
  "type_code" TEXT,
  "type_code_system" TEXT,
  "type_display" TEXT
);

-- document_references: 51 records, 13 columns
CREATE TABLE IF NOT EXISTS document_references (
  "document_reference_content_data" TEXT,
  "document_reference_content_type" TEXT,
  "document_reference_id" TEXT,
  "document_reference_type" TEXT,
  "document_reference_type_code" TEXT,
  "document_reference_type_code_snomed" TEXT,
  "document_reference_type_code_snomed_name" TEXT,
  "document_reference_type_coding_system" TEXT,
  "encounter_reference_id" TEXT,
  "last_updated" TEXT,
  "patient_id" TEXT,
  "practitioner_role_reference_id" TEXT,
  "subject_patient_id" TEXT
);

-- encounters: 5 records, 19 columns
CREATE TABLE IF NOT EXISTS encounters (
  "condition_id_references" TEXT,
  "encounter_end_time" TEXT,
  "encounter_id" TEXT,
  "encounter_start_time" TEXT,
  "encounter_text" TEXT,
  "encounter_type_code" TEXT,
  "encounter_type_code_cpt" TEXT,
  "encounter_type_code_cpt_name" TEXT,
  "encounter_type_code_icd10" TEXT,
  "encounter_type_code_icd10_name" TEXT,
  "encounter_type_code_snomed" TEXT,
  "encounter_type_code_snomed_name" TEXT,
  "encounter_type_code_system" TEXT,
  "encounter_type_name" TEXT,
  "hospitalization_discharge_disposition" TEXT,
  "location_id_references" TEXT,
  "patient_id" TEXT,
  "practitioner_role_id_references" TEXT,
  "subject_patient_id" TEXT
);

-- family_member_histories: 0 records, 11 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS family_member_histories (
  "family_member_history_condition_code" TEXT,
  "family_member_history_condition_code_system" TEXT,
  "family_member_history_condition_display" TEXT,
  "family_member_history_id" TEXT,
  "family_member_history_relationship_code" TEXT,
  "family_member_history_relationship_code_system" TEXT,
  "family_member_history_relationship_display" TEXT,
  "family_member_history_sex_code" TEXT,
  "family_member_history_sex_code_system" TEXT,
  "family_member_history_sex_display" TEXT,
  "patient_id" TEXT
);

-- immunizations: 0 records, 27 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS immunizations (
  "immunization_code" TEXT,
  "immunization_code_cvx" TEXT,
  "immunization_code_cvx_name" TEXT,
  "immunization_code_ndc" TEXT,
  "immunization_code_ndc_name" TEXT,
  "immunization_code_rxnorm" TEXT,
  "immunization_code_rxnorm_name" TEXT,
  "immunization_code_snomed" TEXT,
  "immunization_code_snomed_name" TEXT,
  "immunization_code_system" TEXT,
  "immunization_dosage_unit" TEXT,
  "immunization_dosage_value" TEXT,
  "immunization_id" TEXT,
  "immunization_lot_number" TEXT,
  "immunization_manufacturer_name" TEXT,
  "immunization_name" TEXT,
  "immunization_occurrence_time" TEXT,
  "immunization_route" TEXT,
  "immunization_route_code" TEXT,
  "immunization_route_code_system" TEXT,
  "immunization_site" TEXT,
  "immunization_site_code" TEXT,
  "immunization_site_code_system" TEXT,
  "immunization_status" TEXT,
  "patient_id" TEXT,
  "performer_practitioner_role_reference_id" TEXT,
  "subject_patient_id" TEXT
);

-- labs: 111 records, 42 columns
CREATE TABLE IF NOT EXISTS labs (
  "diagnostic_interpreter_practitioner_role_reference_id" TEXT,
  "diagnostic_performer_practitioner_role_reference_id" TEXT,
  "diagnostic_report_code" TEXT,
  "diagnostic_report_code_cpt" TEXT,
  "diagnostic_report_code_cpt_name" TEXT,
  "diagnostic_report_code_loinc" TEXT,
  "diagnostic_report_code_loinc_name" TEXT,
  "diagnostic_report_code_snomed" TEXT,
  "diagnostic_report_code_snomed_name" TEXT,
  "diagnostic_report_code_system" TEXT,
  "diagnostic_report_id" TEXT,
  "diagnostic_report_name" TEXT,
  "lab_code" TEXT,
  "lab_code_cpt" TEXT,
  "lab_code_cpt_name" TEXT,
  "lab_code_loinc" TEXT,
  "lab_code_loinc_name" TEXT,
  "lab_code_snomed" TEXT,
  "lab_code_snomed_name" TEXT,
  "lab_code_system" TEXT,
  "lab_interpretation" TEXT,
  "lab_name" TEXT,
  "lab_observation_id" TEXT,
  "lab_reference_range_high" TEXT,
  "lab_reference_range_interpretation" TEXT,
  "lab_reference_range_interpretation_code" TEXT,
  "lab_reference_range_low" TEXT,
  "lab_reference_range_text" TEXT,
  "lab_reference_range_unit" TEXT,
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

-- medication_fills: 0 records, 35 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS medication_fills (
  "code_list_qualifier" TEXT,
  "days_supply" TEXT,
  "dea_schedule" TEXT,
  "directions" TEXT,
  "electronic_prescription" TEXT,
  "history_source_fill_number" TEXT,
  "last_filled_date" TEXT,
  "medication_id" TEXT,
  "medication_name" TEXT,
  "medication_statement_start_time" TEXT,
  "ndc_code" TEXT,
  "patient_id" TEXT,
  "pharmacy_city" TEXT,
  "pharmacy_ncpdp_id" TEXT,
  "pharmacy_npi" TEXT,
  "pharmacy_state" TEXT,
  "pharmacy_store_name" TEXT,
  "prescriber_name" TEXT,
  "prescriber_npi" TEXT,
  "prescription_number" TEXT,
  "product_code" TEXT,
  "quantity_prescribed" TEXT,
  "quantity_unit_code" TEXT,
  "record_id" TEXT,
  "refills_qualifier" TEXT,
  "refills_value" TEXT,
  "rxcui" TEXT,
  "sent_time" TEXT,
  "sold_date" TEXT,
  "strength" TEXT,
  "strength_code" TEXT,
  "strength_source_code" TEXT,
  "substitutions" TEXT,
  "unit_source_code" TEXT,
  "written_date" TEXT
);

-- medications: 6 records, 25 columns
CREATE TABLE IF NOT EXISTS medications (
  "medication_code" TEXT,
  "medication_code_ndc" TEXT,
  "medication_code_ndc_name" TEXT,
  "medication_code_rxnorm" TEXT,
  "medication_code_rxnorm_name" TEXT,
  "medication_code_snomed" TEXT,
  "medication_code_snomed_name" TEXT,
  "medication_code_system" TEXT,
  "medication_context" TEXT,
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

-- problems: 5 records, 18 columns
CREATE TABLE IF NOT EXISTS problems (
  "condition_category_code" TEXT,
  "condition_category_code_name" TEXT,
  "condition_category_code_system" TEXT,
  "condition_clinical_status" TEXT,
  "condition_code" TEXT,
  "condition_code_icd10" TEXT,
  "condition_code_icd10_name" TEXT,
  "condition_code_snomed" TEXT,
  "condition_code_snomed_name" TEXT,
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

-- procedures: 4 records, 22 columns
CREATE TABLE IF NOT EXISTS procedures (
  "asserter_practitioner_role_reference_id" TEXT,
  "encounter_reference_id" TEXT,
  "patient_id" TEXT,
  "performer_practitioner_role_reference_id" TEXT,
  "procedure_code" TEXT,
  "procedure_code_cpt" TEXT,
  "procedure_code_cpt_name" TEXT,
  "procedure_code_snomed" TEXT,
  "procedure_code_snomed_name" TEXT,
  "procedure_code_system" TEXT,
  "procedure_date_time" TEXT,
  "procedure_id" TEXT,
  "procedure_name" TEXT,
  "procedure_reason" TEXT,
  "procedure_reason_code" TEXT,
  "procedure_reason_code_icd10" TEXT,
  "procedure_reason_code_icd10_name" TEXT,
  "procedure_reason_code_snomed" TEXT,
  "procedure_reason_code_snomed_name" TEXT,
  "procedure_reason_code_system" TEXT,
  "procedure_text" TEXT,
  "subject_patient_id" TEXT
);

-- record_sources: 307 records, 6 columns
CREATE TABLE IF NOT EXISTS record_sources (
  "document_reference_id" TEXT,
  "patient_id" TEXT,
  "resource_id" TEXT,
  "resource_id_name" TEXT,
  "resource_type" TEXT,
  "source_id" TEXT
);

-- social_histories: 0 records, 17 columns (columns from the FLAT data contract)
CREATE TABLE IF NOT EXISTS social_histories (
  "observation_category" TEXT,
  "patient_id" TEXT,
  "practitioner_role_reference_id" TEXT,
  "social_history_observation_code" TEXT,
  "social_history_observation_code_loinc" TEXT,
  "social_history_observation_code_loinc_name" TEXT,
  "social_history_observation_code_snomed" TEXT,
  "social_history_observation_code_snomed_name" TEXT,
  "social_history_observation_code_system" TEXT,
  "social_history_observation_id" TEXT,
  "social_history_observation_name" TEXT,
  "social_history_observation_timestamp" TEXT,
  "social_history_observation_value" TEXT,
  "social_history_observation_value_code" TEXT,
  "social_history_observation_value_code_system" TEXT,
  "social_history_text" TEXT,
  "subject_patient_id" TEXT
);

-- sources: 6 records, 12 columns
CREATE TABLE IF NOT EXISTS sources (
  "author_name" TEXT,
  "class_code" TEXT,
  "event_code" TEXT,
  "healthcare_facility_type_code" TEXT,
  "patient_id" TEXT,
  "practice_setting_code" TEXT,
  "service_end_time" TEXT,
  "service_start_time" TEXT,
  "source_id" TEXT,
  "source_name" TEXT,
  "title" TEXT,
  "type" TEXT
);

-- transitions: 2 records, 38 columns
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
  "discharge_disposition_code_hl7" TEXT,
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
  "possible_observation_stays" TEXT,
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

-- vital_signs: 116 records, 16 columns
CREATE TABLE IF NOT EXISTS vital_signs (
  "observation_category" TEXT,
  "patient_id" TEXT,
  "subject_patient_id" TEXT,
  "vital_sign_grouping_observation_id" TEXT,
  "vital_sign_observation_code" TEXT,
  "vital_sign_observation_code_loinc" TEXT,
  "vital_sign_observation_code_loinc_name" TEXT,
  "vital_sign_observation_code_snomed" TEXT,
  "vital_sign_observation_code_snomed_name" TEXT,
  "vital_sign_observation_code_system" TEXT,
  "vital_sign_observation_id" TEXT,
  "vital_sign_observation_name" TEXT,
  "vital_sign_observation_text" TEXT,
  "vital_sign_observation_time" TEXT,
  "vital_sign_observation_unit" TEXT,
  "vital_sign_observation_value" TEXT
);
