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
| address_state | str | Yes | Two-letter abbreviation (e.g., "MA") |
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

### Signal Models (`particle-api-quickstarts/src/particle/signal/models.py`)

**SubscriptionType** (enum): `MONITORING`

**WorkflowType** (enum): `ADMIT_TRANSITION_ALERT | DISCHARGE_TRANSITION_ALERT | TRANSFER_TRANSITION_ALERT | NEW_ENCOUNTER_ALERT | REFERRAL_ALERT | ADT | DISCHARGE_SUMMARY_ALERT`

**ADTEventType** (enum): `A01 | A02 | A03 | A04 | A08`

**Subscription**: `type: SubscriptionType` (default: MONITORING)

**SubscriptionResponse**: `id: str, type: SubscriptionType` (extra="ignore")

**SubscribeResponse**: `subscriptions: list[SubscriptionResponse]` (default: [])

**TriggerSandboxWorkflowRequest**:

| Field | Type | Required | Default |
|-------|------|----------|---------|
| workflow | WorkflowType | Yes | — |
| callback_url | str | Yes | — |
| display_name | str | No | "Test" |
| event_type | ADTEventType | Only for ADT workflow | None |

**ReferralOrganization**: `oid: str` (min_length=1)

**TransitionResource**: `file_id: str, resource_ids: list[str]` (extra="ignore")

**WebhookNotificationData** (CloudEvents data payload):

| Field | Type | Notes |
|-------|------|-------|
| particle_patient_id | str | Required |
| event_type | str | None | e.g., "A01" |
| event_sequence | int | None | Order within event stream |
| is_final_event | bool | None | True when stream is complete |
| resources | list[TransitionResource] | File IDs + resource paths |

**WebhookNotification** (CloudEvents 1.0 envelope):

| Field | Type | Default |
|-------|------|---------|
| specversion | str | "1.0" |
| type | str | e.g., "com.particlehealth.api.v2.transitionalerts" |
| subject | str | None |
| source | str | None |
| id | str | Notification UUID |
| time | datetime | None |
| datacontenttype | str | None |
| data | WebhookNotificationData | Required |

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

**CreateNotificationRequest**:
| Field | Type | Default |
|-------|------|---------|
| display_name | str | — |
| notification_type | str | — (query, patient, networkalert, hl7v2) |
| callback_url | str | — |
| active | bool | True |

**UpdateNotificationRequest**: `display_name: str | None, callback_url: str | None, active: bool | None`

**Notification**: `name, display_name, notification_type, callback_url, active, create_time, update_time`

**SignatureKey**: `name, signature_key, create_time, update_time`

**CreateSignatureKeyRequest**: `signature_key: str`

## Flat Data Resource Types

When loaded into a database or a data warehouse, each resource type becomes a table. All columns are TEXT/STRING.

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
