# Flat Data Contract

Particle Health FLAT Data Format Specification v2.3.1 — defines the structure, format, and semantics of flattened clinical data delivered through the Particle Health platform.

Based on Open Data Contract Standard (ODCS) v3. Source: `ParticleFlatDataContract_v2.3.1.xlsx`.

## Contract Metadata

| Property | Value |
|----------|-------|
| Kind | DataContract |
| API Version | v3.0.2 |
| Contract Version | 2.3.1 |
| Status | In development |
| Owner | Product |
| Domain | clinical-data |
| Data Product | Workbench |
| Tenant | Particle Health |
| Purpose | Defines structure for a flattened, relational model of clinical data derived from CCDA documents |
| Usage | Treatment workflows, analytics, reporting, and downstream integration |

## Infrastructure

| Property | Value |
|----------|-------|
| Server | production |
| Type | BigQuery |
| Project | ParticleHealth |
| Dataset | clinical_flat |

## Schema Overview

All columns are `TEXT/STRING` unless otherwise noted. Every table includes `patient_id` (UUID) as a foreign key to the Patients table.

| Table | Columns | Primary Key | Description |
|-------|---------|-------------|-------------|
| [Allergies](#allergies) | 13 | allergy_id | Allergy and intolerance data |
| [AIOutputs](#aioutputs) | 6 | ai_output_id | AI-generated clinical summaries (Snapshot add-on) |
| [AICitations](#aicitations) | 6 | citation_id | Source citations for AI outputs (Snapshot add-on) |
| [Coverages](#coverages) | 20 | coverage_id | Insurance coverage and payor information |
| [DocumentReferences](#documentreferences) | 10 | document_reference_id | Clinical document metadata |
| [Encounters](#encounters) | 13 | encounter_id | Patient-provider interactions (visits, admissions) |
| [FamilyMemberHistories](#familymemberhistories) | 11 | family_member_history_id | Family medical history |
| [Immunizations](#immunizations) | 19 | immunization_id | Vaccine administration records |
| [Labs](#labs) | 22 | lab_observation_id | Laboratory test results |
| [Locations](#locations) | 10 | location_id | Healthcare facility information |
| [Medications](#medications) | 18 | medication_id | Prescription and medication records |
| [MedicationFills](#medicationfills) | 35 | record_id | Dispensed medication fills (Surescripts add-on) |
| [Organizations](#organizations) | 12 | organization_id | Healthcare organization details |
| [Patients](#patients) | 15 | patient_id | Core patient demographics |
| [Practitioners](#practitioners) | 20 | practitioner_role_id | Healthcare provider information |
| [Problems](#problems) | 14 | condition_id | Clinical conditions and diagnoses |
| [Procedures](#procedures) | 14 | procedure_id | Clinical procedure records |
| [SocialHistories](#socialhistories) | 13 | social_history_observation_id | Lifestyle and behavioral observations |
| [Transitions](#transitions) | 33 | transition_id | Care transitions (admit/discharge/transfer) |
| [VitalSigns](#vitalsigns) | 12 | vital_sign_observation_id | Vital sign measurements |
| [RecordSources](#recordsources) | 6 | resource_id | Provenance bridge linking rows to source files |
| [Sources](#sources) | 3 | source_id | Ingested clinical file inventory |

## Key Relationships

```
Sources (source_id)
  └── RecordSources (source_id → Sources.source_id)
        └── [Any clinical table] (resource_id → RecordSources.resource_id)

Patients (patient_id)
  └── Every table references patients.patient_id

Encounters (encounter_id)
  ├── Problems (encounter_id → encounters.encounter_id)
  ├── Procedures (encounter_reference_id → encounters.encounter_id)
  └── DocumentReferences (encounter_reference_id → encounters.encounter_id)

Practitioners (practitioner_role_id)
  ├── Allergies (practitioner_role_id)
  ├── Medications (practitioner_role_id)
  ├── Immunizations (performer_practitioner_role_reference_id)
  ├── Labs (diagnostic_interpreter/performer_practitioner_role_reference_id)
  └── SocialHistories (practitioner_role_reference_id)

AIOutputs (ai_output_id)
  └── AICitations (ai_output_id → AIOutputs.ai_output_id)

Medications (medication_id)
  └── MedicationFills (medication_id → Medications.medication_id)
```

## Physical Type Reference

| Physical Type | Description | Example |
|---------------|-------------|---------|
| uuid | UUID v4 | `05a2239f-9c86-4735-8197-591324cc9ee6` |
| sha256_hash | Hex-encoded SHA-256 | `89299a2460139...` (64 chars) |
| string | Free text | — |
| uri | OID or URI | `urn:oid:2.16.840.1.113883.6.88` |
| timestamp | ISO 8601 with timezone | `2024-01-15T10:30:00-05:00` |
| datetime | Date/time | `2024-01-15T10:30:00` |
| int | Integer | `1` |
| float | Decimal number | `98.6` |
| double | Double-precision float | `0.5` |
| boolean | True/false | `true` |
| xml | Raw XML content | — |

## Table Schemas

### Allergies

Contains allergy and intolerance data, including allergen, reaction, severity, and recording practitioner.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier from query POST |
| allergy_id | string | sha256_hash | Yes | Yes | SHA-256 hash uniquely identifying the allergy record |
| practitioner_role_id | string | sha256_hash | No | | References practitioners.practitioner_role_id |
| subject_patient_id | string | sha256_hash | No | | References patients.resource_id |
| allergy_code | string | string | No | | Codes identifying the allergy, pipe-delimited |
| allergy_code_system | string | uri | No | | Code system URIs, comma-delimited |
| allergy_name | string | string | No | | Description of the allergy or intolerance |
| allergy_onset_start | date | timestamp | No | | Date manifestations started |
| allergy_onset_end | date | timestamp | No | | Date manifestations ended |
| reaction_manifestation | string | string | No | | Symptoms associated with a reaction |
| reaction_manifestation_code | string | string | No | | Code for reaction symptoms |
| reaction_manifestation_code_system | string | uri | No | | Code system for reaction codes |
| recorded_date | date | timestamp | No | | Date the allergy was recorded |

### AIOutputs

AI-generated clinical summaries. **Snapshot product add-on.**

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| ai_output_id | string | uuid | Yes | Yes | Unique AI output identifier |
| type | string | string | Yes | | Output classification (summary type) |
| text | string | string | Yes | | AI-generated clinical summary text |
| resource_reference_id | array | string | No | | Source resource IDs used for generation |
| created_timestamp | timestamp | datetime | Yes | | When the output was generated |

### AICitations

Source citations linking AI outputs to clinical data. **Snapshot product add-on.**

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| ai_output_id | string | uuid | Yes | | References AIOutputs.ai_output_id |
| citation_id | string | uuid | Yes | Yes | Unique citation identifier |
| resource_reference_id | string | string | Yes | | Hash reference to source FLAT table row |
| resource_type | string | string | Yes | | FLAT table name containing source data |
| text_snippet | string | string | Yes | | Excerpt from source document supporting the AI statement |

### Coverages

Insurance coverage information including subscriber details, payor references, and relationship codes.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| coverage_id | string | uuid | Yes | Yes | Unique coverage identifier |
| coverage_subscriber_id | string | sha256_hash | No | | Subscriber identifier |
| coverage_class_type_code | string | string | No | | Class type code (group, plan) |
| coverage_class_type_code_system | string | uri | No | | Code system for class type |
| coverage_class_type_display | string | string | No | | Display value (employee, dependent, self-pay) |
| coverage_class_value | string | string | No | | Payer-assigned class identifier |
| coverage_identifier_value | string | string | No | | Policy/group number |
| coverage_identifier_system | string | string | No | | OID of issuing system |
| coverage_order | integer | int | No | | Coverage priority (0=primary, 1=secondary) |
| coverage_payor_reference | string | uuid | No | | References organization_id |
| coverage_relationship_code | string | string | No | | Insured-to-subscriber relationship code |
| coverage_relationship_code_system | string | uri | No | | Code system for relationship |
| coverage_relationship_display | string | string | No | | Relationship description |
| coverage_status | string | string | No | | ACTIVE, CANCELLED, or EXPIRED |
| coverage_subscriber_reference | string | sha256_hash | No | | Subscriber reference hash |
| coverage_type_code | string | string | No | | Coverage type (Medicare, Medicaid, commercial) |
| coverage_type_code_system | string | uri | No | | Code system for coverage type |
| coverage_type_display | string | string | No | | Coverage type display text |
| coverage_beneficiary_reference | string | uuid | No | | Beneficiary reference |

### DocumentReferences

Metadata about clinical documents (summaries, diagnostic reports, scanned images).

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| document_reference_id | string | uuid | No | Yes | Unique document reference ID |
| encounter_reference_id | string | uuid | No | | References encounters.encounter_id |
| document_reference_content_data | string | xml | No | | Raw XML content from the document |
| document_reference_content_type | string | string | No | | MIME type (text/plain, application/xml) |
| document_reference_type_code | string | string | No | | Document type code (LOINC, ActCode) |
| document_reference_type_coding_system | string | string | No | | Code system OIDs |
| document_reference_type | string | string | No | | Human-readable document type |
| practitioner_role_reference_id | string | string | No | | Not implemented (always null) |
| subject_patient_id | string | string | No | | References patients.resource_id |

### Encounters

Patient-provider interactions (clinic visits, hospital admissions, ER stays, telehealth).

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| encounter_id | string | sha256_hash | Yes | Yes | Unique encounter identifier |
| patient_id | string | uuid | Yes | | Patient identifier |
| subject_patient_id | string | string | No | | References patients.resource_id |
| condition_id_references | string | string | No | | SHA-256 condition IDs, comma-delimited |
| location_id_references | string | string | No | | SHA-256 location IDs, comma-delimited |
| practitioner_role_id_references | string | string | No | | SHA-256 practitioner role IDs, comma-delimited |
| encounter_end_time | date | timestamp | No | | Encounter end timestamp |
| encounter_start_time | date | timestamp | No | | Encounter start timestamp |
| encounter_text | string | string | No | | Not implemented (always null) |
| encounter_type_code | string | string | No | | Encounter type codes (ambulatory, emergency) |
| encounter_type_code_system | string | uri | No | | Code systems for encounter type |
| encounter_type_name | string | string | No | | Human-readable encounter type |
| hospitalization_discharge_disposition | string | string | No | | Discharge destination description |

### FamilyMemberHistories

Family medical history — conditions, relationships, sex, and age at onset.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| family_member_history_id | string | uuid | Yes | Yes | Unique family history record ID |
| family_member_history_condition_code | string | string | No | | Condition code (typically SNOMED CT) |
| family_member_history_condition_display | string | string | No | | Condition description (e.g., Stroke, Diabetes) |
| family_member_history_condition_code_system | string | uri | No | | Code system (typically SNOMED CT) |
| family_member_history_relationship_code | string | string | No | | Relationship code (mother, brother) |
| family_member_history_relationship_display | string | string | No | | Relationship description |
| family_member_history_relationship_code_system | string | uri | No | | Relationship code system |
| family_member_history_sex_code | string | string | No | | Sex code (M, F) |
| family_member_history_sex_display | string | string | No | | Sex description |
| family_member_history_sex_code_system | string | uri | No | | Sex code system |

### Immunizations

Vaccine administration records including type, manufacturer, lot number, and route.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| immunization_id | string | uuid | Yes | Yes | Unique immunization record ID |
| immunization_code | string | string | No | | CVX, CPT, or NDC codes, comma-delimited |
| immunization_code_system | string | uri | No | | Code systems |
| immunization_name | string | string | No | | Vaccine name/description |
| immunization_dosage_value | number | float | No | | Dose amount (e.g., 0.5) |
| immunization_dosage_unit | string | string | No | | Unit of measure (e.g., mL) |
| immunization_lot_number | string | string | No | | Manufacturer lot number |
| immunization_manufacturer_name | string | string | No | | Vaccine manufacturer |
| immunization_occurrence_time | date | timestamp | No | | Administration date/time |
| immunization_route_code | string | string | No | | Route code (SNOMED CT) |
| immunization_route_code_system | string | uri | No | | Route code system |
| immunization_route | string | string | No | | Route description (Intramuscular, Subcutaneous) |
| immunization_site_code | string | string | No | | Anatomical site code |
| immunization_site_code_system | string | uri | No | | Site code system |
| immunization_site | string | string | No | | Anatomical site description |
| performer_practitioner_role_reference_id | string | sha256_hash | No | | References practitioners.practitioner_role_id |
| immunization_status | string | string | No | | Status (completed, entered-in-error, not done) |
| subject_patient_id | string | string | No | | References patients.resource_id |

### Labs

Laboratory test results with values, units, reference ranges, and interpretation.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| lab_observation_id | string | uuid | Yes | Yes | Unique lab observation ID |
| subject_patient_id | string | string | No | | References patients.resource_id |
| diagnostic_interpreter_practitioner_role_reference_id | string | sha256_hash | No | | Interpreting practitioner reference |
| diagnostic_performer_practitioner_role_reference_id | string | sha256_hash | No | | Performing practitioner reference |
| diagnostic_report_id | string | sha256_hash | No | | Grouper for related lab observations |
| diagnostic_report_name | string | string | No | | Report/panel name |
| lab_code | string | string | No | | Lab code (typically LOINC) |
| lab_code_system | string | uri | No | | Code system |
| lab_interpretation | string | string | No | | Result interpretation (Abnormal, High, Low) |
| lab_name | string | string | No | | Test name (e.g., CALCIUM, POTASSIUM) |
| lab_text | string | string | No | | Always null — will be sunset |
| lab_timestamp | date | timestamp | No | | Result timestamp |
| lab_unit | string | string | No | | Measurement unit (g/dL, mmol/L) |
| lab_unit_quantity | string | string | No | | UCUM unit for quantitative value |
| lab_value | string | string | No | | Raw value (numeric or categorical) |
| lab_value_boolean | boolean | boolean | No | | Boolean result (presence/detection) |
| lab_value_code | string | string | No | | Coded result value |
| lab_value_code_system | string | uri | No | | Code system for value code |
| lab_value_quantity | number | float | No | | Numeric result value |
| lab_value_string | string | string | No | | Free-text result |
| observation_category | string | string | No | | Always "laboratory" |

### Locations

Healthcare facilities and care delivery sites.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| location_id | string | uuid | Yes | Yes | Unique location ID |
| location_name | string | string | No | | Facility or site name |
| location_address | string | string | No | | Street address |
| location_city | string | string | No | | City |
| location_postal_code | string | string | No | | ZIP/postal code |
| location_state | string | string | No | | U.S. state abbreviation |
| location_type | string | string | No | | Location category, comma-delimited |
| location_type_code | string | string | No | | Location type code (NUCC) |
| location_type_code_system | string | uri | No | | Code system for location type |

### Medications

Prescription and medication records from clinical documents.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| medication_id | string | uuid | Yes | Yes | Unique medication record ID |
| practitioner_role_id | string | sha256_hash | No | | Prescribing provider reference |
| subject_patient_id | string | string | No | | References patients.resource_id |
| medication_code | string | string | No | | Medication codes, comma-delimited |
| medication_code_system | string | uri | No | | Code systems |
| medication_name | string | string | No | | Full medication name with dosage info |
| medication_reference | string | string | No | | Always null (backwards compat) |
| medication_resource_type | string | string | No | | Always `medication_statement` |
| medication_statement_dose_route | string | string | No | | Route (Oral, Intramuscular) |
| medication_statement_dose_unit | string | string | No | | Dose unit |
| medication_statement_dose_value | number | double | No | | Dose amount |
| medication_statement_end_time | date | datetime | No | | Usage period end |
| medication_statement_id | string | string | No | | Always null (backwards compat) |
| medication_statement_patient_instructions | string | string | No | | Instructions for the patient |
| medication_statement_start_time | date | datetime | No | | Usage period start |
| medication_statement_status | string | string | No | | Status (active, completed) |
| medication_statement_text | string | string | No | | May be null in all records |

### MedicationFills

Dispensed medication fill events from Surescripts. **Surescripts Integration add-on.**

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| record_id | string | uuid | Yes | Yes | Unique fill record ID |
| medication_id | string | uuid | Yes | | References Medications.medication_id |
| strength | string | string | No | | Dosage strength |
| strength_source_code | string | string | No | | Surescripts strength source code |
| strength_code | string | string | No | | Internal strength code |
| code_list_qualifier | string | string | No | | Classification system qualifier |
| unit_source_code | string | string | No | | Unit of measure source code |
| quantity_unit_code | string | string | No | | Potency unit code |
| days_supply | integer | int | No | | Days of medication supplied |
| directions | string | string | No | | Dosing instructions |
| refills_value | integer | int | No | | Authorized refills count |
| refills_qualifier | string | string | No | | Refills interpretation qualifier |
| substitutions | integer | int | No | | Substitution allowed (0 or 1) |
| product_code | string | string | No | | Drug product identifier |
| written_date | date | datetime | No | | Prescription written date |
| last_filled_date | date | datetime | No | | Last fill date |
| sold_date | date | datetime | No | | Date sold to patient |
| ndc_code | string | string | No | | National Drug Code (hyphenated) |
| rxcui | integer | int | No | | RxNorm Concept Unique Identifier |
| medication_statement_start_time | date | datetime | No | | Medication statement start |
| medication_name | string | string | No | | Dispensed medication name |
| quantity_prescribed | integer | int | No | | Prescribed quantity |
| dea_schedule | string | string | No | | DEA drug classification |
| prescription_number | string | string | No | | Pharmacy-assigned prescription number |
| pharmacy_npi | string | string | No | | Dispensing pharmacy NPI |
| pharmacy_ncpdpid | string | string | No | | Pharmacy NCPDP ID |
| pharmacy_store_name | string | string | No | | Pharmacy name |
| pharmacy_city | string | string | No | | Pharmacy city |
| pharmacy_state | string | string | No | | Pharmacy state abbreviation |
| prescriber_npi | string | string | No | | Prescriber NPI |
| prescriber_name | string | string | No | | Prescriber full name |
| electronic_prescription | boolean | bool | No | | Was prescription electronic |
| sent_time | date | datetime | No | | Surescripts message timestamp |

### Organizations

Healthcare organizations involved in patient care.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| organization_id | string | sha256_hash | Yes | Yes | Unique organization ID |
| organization_name | string | string | No | | Organization name |
| organization_address_lines | string | string | No | | Street address, comma-delimited |
| organization_address_city | string | string | No | | City |
| organization_address_state | string | string | No | | State abbreviation |
| organization_address_postal_code | string | string | No | | Postal code |
| organization_address_country | string | string | No | | ISO 3166-1 alpha-2 country code |
| organization_address_use | string | string | No | | Address use (work, home) |
| organization_telecom_value | string | string | No | | Phone/fax number |
| organization_telecom_use | string | string | No | | Telecom use (work) |
| organization_telecom_system | string | string | No | | Telecom system type, comma-delimited |

### Patients

Core patient demographics and administrative data.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | Yes | Patient identifier from query POST |
| resource_id | string | sha256_hash | No | | Internal patient resource tracker |
| address_city | string | string | No | | City |
| address_county | string | string | No | | County |
| address_line | string | string | No | | Street address |
| address_postal_code | string | string | No | | Postal code |
| address_state | string | string | No | | U.S. state abbreviation |
| date_of_birth | date | datetime | No | | Date of birth |
| family_name | string | string | No | | Last name(s) |
| given_name | string | string | No | | First/middle names, comma-delimited |
| gender | string | string | No | | Gender from source document |
| language | string | string | No | | Languages, comma-delimited |
| marital_status | string | string | No | | Marital status |
| race | string | string | No | | Race/ethnicity, comma-delimited |
| telephone | string | string | No | | Phone numbers, comma-delimited |

### Practitioners

Healthcare practitioners with roles, specialties, and contact information.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| patient_id | string | uuid | Yes | | Patient identifier |
| practitioner_role_specialty_code | string | string | No | | Specialty codes, comma-delimited |
| practitioner_address_city | string | string | No | | City |
| practitioner_address_state | string | string | No | | State |
| practitioner_address_street | string | string | No | | Street address |
| practitioner_address_use | string | string | No | | Address use (work, home) |
| practitioner_family_name | string | string | No | | Last name |
| practitioner_given_name | string | string | No | | Given names (may include credentials) |
| practitioner_id | string | sha256_hash | Yes | | Person identifier — NOT unique in this table |
| practitioner_identifier_system | string | uri | No | | Credential system identifiers |
| practitioner_identifier_value | string | string | No | | Credential values (often NPIs) |
| practitioner_name_suffix | string | string | No | | Name suffix |
| practitioner_role | string | string | No | | Role relative to patient |
| practitioner_role_code | string | string | No | | Role codes, comma-delimited |
| practitioner_role_code_system | string | uri | No | | Role code systems |
| practitioner_role_id | string | sha256_hash | Yes | Yes | Unique practitioner-in-role ID |
| practitioner_role_specialty | string | string | No | | Specialty description |
| practitioner_role_specialty_code_system | string | uri | No | | Specialty code systems |
| practitioner_telecom_system | string | string | No | | Contact methods (PHONE, EMAIL) |
| practitioner_telecom_value | string | string | No | | Contact information |

**Important:** `practitioner_id` identifies the person but is NOT unique — the same practitioner can appear in multiple roles. Use `practitioner_role_id` as the primary key.

### Problems

Clinical conditions, diagnoses, and problem list items.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| condition_id | string | sha256_hash | Yes | Yes | Unique condition ID |
| patient_id | string | uuid | Yes | | Patient identifier |
| subject_patient_id | string | string | No | | References patients.resource_id |
| encounter_id | string | sha256_hash | No | | References encounters.encounter_id |
| condition_category_code | string | string | No | | Classification (problem list, encounter diagnosis) |
| condition_category_code_name | string | string | No | | Category description |
| condition_category_code_system | string | uri | No | | Category code system |
| condition_code | string | string | No | | Condition/diagnosis codes |
| condition_code_system | string | uri | No | | Code systems (ICD-10, SNOMED) |
| condition_name | string | string | No | | Human-readable condition description |
| condition_clinical_status | string | string | No | | Status (active, resolved) |
| condition_onset_date | date | datetime | No | | Condition onset date/time |
| condition_recorded_date | date | datetime | No | | Date recorded in patient record |
| condition_text | string | string | No | | Not implemented (always null) |

### Procedures

Clinical procedures performed on patients.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| procedure_id | string | uuid | Yes | Yes | Unique procedure ID |
| patient_id | string | uuid | Yes | | Patient identifier |
| asserter_practitioner_role_reference_id | string | string | No | | Not implemented |
| encounter_reference_id | string | sha256_hash | No | | References encounters.encounter_id |
| performer_practitioner_role_reference_id | string | string | No | | Not implemented |
| procedure_code | string | string | No | | Procedure codes |
| procedure_code_system | string | uri | No | | Code systems |
| procedure_date_time | date | datetime | No | | When the procedure was performed |
| procedure_name | string | string | No | | Procedure description |
| procedure_reason | string | string | No | | Clinical reason |
| procedure_reason_code | string | string | No | | Reason code |
| procedure_reason_code_system | string | uri | No | | Reason code system |
| procedure_text | string | string | No | | Not implemented |
| subject_patient_id | string | string | No | | References patients.resource_id |

### SocialHistories

Lifestyle and behavioral observations (tobacco, alcohol, habits).

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| social_history_observation_id | string | sha256_hash | Yes | Yes | Unique observation ID |
| patient_id | string | uuid | Yes | | Patient identifier |
| subject_patient_id | string | string | No | | References patients.resource_id |
| practitioner_role_reference_id | string | sha256_hash | No | | Documenting practitioner reference |
| observation_category | string | string | Yes | | Always "social-history" |
| social_history_observation_code | string | string | No | | Observation type code |
| social_history_observation_code_system | string | uri | No | | Code system |
| social_history_observation_name | string | string | No | | Observation description |
| social_history_observation_timestamp | date | datetime | No | | When the observation was recorded |
| social_history_observation_value_code | string | string | No | | Value/outcome code |
| social_history_observation_value_code_system | string | uri | No | | Value code system |
| social_history_observation_value | string | string | No | | Human-readable outcome |
| social_history_text | string | string | No | | Not implemented (reserved) |

### Transitions

Care transition events (admit, discharge, transfer, death). Used by Signal/ADT workflows.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| transition_id | string | uuid | Yes | Yes | Unique transition record ID |
| visit_id | string | uuid | Yes | | Event/visit identifier |
| particle_patient_id | string | uuid | Yes | | Patient identifier |
| last_name | string | string | No | | Patient last name |
| first_name | string | string | No | | Patient first name |
| dob | date | datetime | No | | Date of birth |
| gender | string | string | No | | Gender |
| address | string | string | No | | Full patient address |
| city | string | string | No | | City |
| state | string | string | No | | State |
| zip | string | string | No | | Postal code |
| phone_number | string | string | No | | Phone number |
| facility_name | string | string | No | | Admitting facility name |
| facility_npi | string | string | No | | Facility NPI |
| facility_type | string | string | No | | Facility type (hospital, SNF, rehab) |
| setting | string | string | Yes | | Event setting (ED, IP, Observation, SNF) |
| status | string | string | Yes | | Visit status (admission, transfer, discharge, death) |
| status_date_time | date | datetime | Yes | | Status update timestamp |
| visit_start_date_time | date | datetime | Yes | | Index encounter start |
| visit_end_date_time | date | datetime | No | | Last encounter end |
| attending_physician_name | string | string | No | | Attending physician name |
| attending_physician_npi | number | integer | No | | Attending physician NPI |
| discharge_diagnosis_code | string | string | No | | Discharge diagnosis codes (can be list) |
| discharge_diagnosis_code_system | string | string | No | | Discharge diagnosis code systems |
| discharge_diagnosis_description | string | string | No | | Discharge diagnosis descriptions |
| discharge_disposition | string | string | No | | Destination at discharge (home, SNF, deceased) |
| discharge_summary | string | string | No | | Clinical summary of hospital stay |
| admitting_diagnosis_code | string | string | No | | Admitting diagnosis codes |
| admitting_diagnosis_code_system | string | string | No | | Admitting diagnosis code systems |
| admitting_diagnosis_description | string | string | No | | Admitting diagnosis descriptions |
| visit_diagnosis_reference_ids | string | string | No | | All diagnoses during the visit |
| visit_encounter_reference_ids | string | string | No | | Encounter IDs during the visit |
| visit_medication_reference_ids | string | string | No | | Medication IDs during the visit |

### VitalSigns

Vital sign measurements (heart rate, blood pressure, temperature).

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| vital_sign_observation_id | string | uuid | Yes | Yes | Unique observation ID |
| patient_id | string | uuid | Yes | | Patient identifier |
| subject_patient_id | string | string | No | | References patients.resource_id |
| observation_category | string | string | No | | Always "vital-signs" |
| vital_sign_grouping_observation_id | string | string | No | | Groups related observations (e.g., systolic + diastolic BP) |
| vital_sign_observation_code | string | string | No | | Observation code (typically LOINC) |
| vital_sign_observation_code_system | string | uri | No | | Code system |
| vital_sign_observation_name | string | string | No | | Vital sign name |
| vital_sign_observation_text | string | string | No | | Free-text description |
| vital_sign_observation_time | date | timestamp | No | | Observation timestamp |
| vital_sign_observation_unit | string | string | No | | Measurement unit |
| vital_sign_observation_value | number | float | No | | Numeric measurement |

### RecordSources

Provenance bridge — links clinical rows to source files. Enables many-to-one tracking without duplicating clinical data.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| resource_id | string | string | Yes | Yes | Unique resource identifier |
| patient_id | string | uuid | Yes | | Patient identifier |
| source_id | string | uuid | Yes | | References Sources.source_id |
| resource_type | string | string | Yes | | Target table (medications, vital_signs, problems) |
| resource_id_name | string | string | No | | PK column name in the resource table |
| document_reference_id | string | string | No | | References DocumentReferences — identifies CCDA section |

### Sources

Inventory of every ingested clinical file.

| Column | Type | Physical Type | Required | PK | Description |
|--------|------|---------------|----------|-----|-------------|
| source_id | string | uuid | Yes | Yes | Unique file identifier |
| patient_id | string | uuid | Yes | | Patient associated with this file |
| source_name | string | string | No | | Human-friendly file name |

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| 2.3.1 | 2026-02-18 | Added new column to RecordSources. Updated unique values in RecordSources and Transitions |
| 2.3.0 | 2025-12-04 | Added AICitations table schema |
| 2.2.1 | 2025-11-13 | Updated column name in MedFills schema |
| 2.2.0 | 2025-10-22 | Added AIOutputs table schema. Updated MedicationFills schema |
| 2.1.2 | 2025-10-08 | Corrected PK and descriptions in Practitioners |
| 2.1.1 | 2025-09-04 | Updated Transitions table schema info |
| 2.1.0 | 2025-06-30 | Added Transitions table schema |
| 2.0.0 | 2025-06-27 | Published initial version |
