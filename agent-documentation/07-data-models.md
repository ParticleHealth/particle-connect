# Data Models

Pydantic models used across the Python SDK and Management UI.

## Query Flow API Models

### Patient Models (`particle-api-quickstarts/src/particle/patient/models.py`)

**Gender** (enum): `MALE | FEMALE`

**PatientRegistration** (request model):

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| given_name | str | Yes | 1-100 chars |
| family_name | str | Yes | 1-100 chars |
| date_of_birth | date | Yes | YYYY-MM-DD |
| gender | Gender | Yes | MALE or FEMALE |
| postal_code | str | Yes | Regex: `^\d{5}(-\d{4})?$` |
| address_city | str | Yes | Min 1 char |
| address_state | str | Yes | Full state name (e.g., "Massachusetts") |
| patient_id | str | Yes | Your external ID |
| address_lines | list[str] | No | — |
| ssn | str | No | Format: XXX-XX-XXXX |
| telephone | str | No | Normalized to XXX-XXX-XXXX |
| email | str | No | — |

Config: `str_strip_whitespace=True`

**PatientResponse** (response model): Same fields as registration plus `particle_patient_id: str`. Config: `extra="ignore"`.

### Query Models (`particle-api-quickstarts/src/particle/query/models.py`)

**PurposeOfUse** (enum): `TREATMENT | PAYMENT | OPERATIONS`

**QueryStatus** (enum): `PENDING | PROCESSING | COMPLETE | PARTIAL | FAILED`

**QueryRequest**:
| Field | Type | Default |
|-------|------|---------|
| purpose_of_use | PurposeOfUse | TREATMENT |

**QuerySubmitResponse**:
| Field | Type |
|-------|------|
| particle_patient_id | str |

**QueryResponse**:
| Field | Type | Notes |
|-------|------|-------|
| query_status | QueryStatus | Aliased from API field "state" |
| files_available | int | Default 0 |
| files_downloaded | int | Default 0 |
| error_message | str | None | Only populated on FAILED |

### Document Models (`particle-api-quickstarts/src/particle/document/models.py`)

**DocumentType** (enum): `CLINICAL`

**MimeType** (enum): `application/xml | application/pdf`

**DocumentSubmission** (request model):

| Field | Type | Required | Default |
|-------|------|----------|---------|
| patient_id | str | Yes | — |
| document_id | str | Yes | — |
| type | DocumentType | No | CLINICAL |
| title | str | Yes | — |
| mime_type | MimeType | Yes | — |
| creation_time | datetime | Yes | — |
| format_code | str | Yes | — |
| class_code | str | Yes | — |
| type_code | str | Yes | — |
| confidentiality_code | str | No | "N" |
| healthcare_facility_type_code | str | No | "394777002" |
| practice_setting_code | str | No | "394733009" |
| service_start_time | datetime | No | None |
| service_stop_time | datetime | No | None |

**DocumentResponse**:
| Field | Type |
|-------|------|
| document_id | str |
| patient_id | str |
| status | str (optional) |

## Management UI Models

### Backend Pydantic Models (`management-ui/backend/app/routers/`)

**CreateProjectRequest**:
| Field | Type | Default |
|-------|------|---------|
| display_name | str | — |
| npi | str | — |
| state | str | "STATE_ACTIVE" |
| commonwell_type | str | "COMMONWELL_TYPE_POSTACUTECARE" |
| address | ProjectAddress | None |

**ProjectAddress**: `line1, city, state, postal_code` (all str, all default "")

**CreateServiceAccountRequest**: `display_name: str = "New Service Account"`

**PolicyBinding**: `role: str, resources: list[str]`

**CreateCredentialRequest**: `oldCredentialTtlHours: int | None`

## Flat Data Resource Types

When loaded into DuckDB/BigQuery, each resource type becomes a table. All columns are TEXT/STRING.

| API Key | Table Name | Key Columns |
|---------|------------|-------------|
| patients | patients | given_name, family_name, date_of_birth, gender |
| labs | labs | lab_name, lab_value, lab_unit, lab_date |
| medications | medications | medication_name, medication_statement_status |
| problems | problems | condition_name, condition_clinical_status |
| encounters | encounters | encounter_type, encounter_start, encounter_end |
| vitalSigns | vital_signs | vital_sign_name, vital_sign_value |
| procedures | procedures | procedure_name, procedure_date |
| practitioners | practitioners | practitioner_name, practitioner_specialty |
| organizations | organizations | organization_name, organization_type |
| documentReferences | document_references | document_type, document_date |
| aIOutputs | ai_outputs | output_type, output_text |
| aICitations | ai_citations | citation_text, source_document_id |
| recordSources | record_sources | source_name, resource_type |
| sources | sources | source_name |
| transitions | transitions | transition_type |
| locations | locations | location_name |
