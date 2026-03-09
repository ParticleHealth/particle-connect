# Notification Data Contract

Webhook notification schemas sent to customer callback URLs. All notifications follow CloudEvents 1.0 and arrive as `POST` requests with `Content-Type: application/cloudevents+json`.

Version: 1.0 (2026-02-05)

## Quick Reference — Notification Types

| Type | CloudEvents `type` | Subject | When it fires |
|------|-------------------|---------|---------------|
| [Transition Alert](#1-transition-alerts) | `com.particlehealth.api.v2.transitionalerts` | Admit/Discharge/Transfer/Death Alert | Patient care transition detected |
| [HL7 ADT](#2-hl7-adt-alerts) | `com.particlehealth.api.v2.hl7v2` | HL7v2 {code} Message for {id} | Raw HL7v2 ADT message received |
| [Query Complete](#3-query-complete) | `com.particlehealth.api.v2.query` | {format} Query Complete | Patient data query finishes |
| [New Encounter](#4-new-encounter-alerts) | `com.particlehealth.api.v2.encounteralerts` | New Encounter | New encounter data available |
| [AI Outputs](#5-ai-outputs-complete) | `com.particlehealth.api.v2.aioutputs` | AI Outputs completed ({n} completed, {m} failed) | AI-generated outputs ready |
| [Consent Updated](#6-patient-consent-updated) | `com.particlehealth.api.v2.consent` | Patient Consent Updated | Patient consent status changes |
| [Medication Fills](#7-medication-fills-data-available) | `com.particlehealth.api.v2.medicationfills` | Medication Fills Data Available | New medication fill data ready |

## HTTP Headers

All notifications include:

```
Content-Type: application/cloudevents+json
Accept: */*
X-Ph-Signature-256: t={unix_timestamp},{hmac_signature}
```

`X-Ph-Signature-256` contains an HMAC SHA-256 signature for verification. See [Signature Verification](#signature-verification).

## Base CloudEvent Envelope

Every notification follows this structure. The `data` field varies by notification type.

| Field | Type | Value | Description |
|-------|------|-------|-------------|
| specversion | string | `"1.0"` | CloudEvents spec version (always 1.0) |
| id | string | UUID | Unique notification event ID |
| source | string | `"api/notifications"` | Event source (always this value) |
| type | string | See table above | Notification type identifier |
| subject | string | Varies | Human-readable event description |
| time | string | ISO 8601 | Event timestamp |
| datacontenttype | string | `"application/json"` | Always application/json |
| data | object | Varies | Notification-specific payload |

## Patient Identifier Fields

These fields appear across multiple notification types. Their meaning is consistent:

| Field | Description |
|-------|-------------|
| `particle_patient_id` | Particle Health's internal patient identifier (UUID) |
| `external_patient_id` | Customer's patient identifier (what you sent during registration) |
| `person_id` | Legacy identifier — only in query notifications |
| `patient_id` | May match `person_id` or `particle_patient_id` depending on context |

## 1. Transition Alerts

**Type:** `com.particlehealth.api.v2.transitionalerts`

Fires when a patient care transition is detected. Four event types share the same schema.

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| network_organization | object | `{ name: string, oid: string, facilities: null \| object }` |
| particle_patient_id | string | Particle patient UUID |
| external_patient_id | string | Customer's patient ID |
| event_type | string | `"admission"` \| `"discharge"` \| `"transfer"` \| `"death"` |
| event_sequence | number | Order in episode (-1 if unknown) |
| is_final_event | string | `"Yes"` \| `"No"` \| `"Unknown"` |
| resources | array | `[{ file_id: string, resource_ids: string[] }]` |

### Subject Values by Event Type

| event_type | subject |
|------------|---------|
| admission | `"Admit Alert"` |
| discharge | `"Discharge Alert"` or `"Discharge Summary Available"` |
| transfer | `"Transfer Alert"` |
| death | `"Death Alert"` |

### Gotchas

- **No facility type in payload.** Transition alerts do NOT include facility type (SNF, Hospital, ED). To get facility type: extract the transition ID from `resources[].resource_ids` (e.g., `transitions/7627990518163879710`), then query the Particle API for full transition details including `facility_type` and `setting`.
- `file_id` may be an empty string (especially for admissions). It contains a value when a discharge summary is available.
- `event_sequence: -1` means the sequence is unknown.

### Example (Admission)

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.transitionalerts",
  "subject": "Admit Alert",
  "source": "api/notifications",
  "id": "1bf79910-543b-4a17-9faa-a7b9d94c5789",
  "time": "2026-02-05T14:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "network_organization": { "name": "", "oid": "", "facilities": null },
    "particle_patient_id": "1bf79910-543b-4a17-9faa-a7b9d94c5789",
    "external_patient_id": "aet200000010175300390098",
    "event_type": "admission",
    "event_sequence": -1,
    "is_final_event": "Unknown",
    "resources": [
      { "file_id": "", "resource_ids": ["transitions/5943578432644100728"] }
    ]
  }
}
```

### Example (Discharge with Summary)

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.transitionalerts",
  "subject": "Discharge Summary Available",
  "source": "api/notifications",
  "id": "2b552992-f56a-4875-a578-ac3e44cbf62c",
  "time": "2026-02-04T07:29:41Z",
  "datacontenttype": "application/json",
  "data": {
    "network_organization": { "name": "", "oid": "", "facilities": null },
    "particle_patient_id": "2b552992-f56a-4875-a578-ac3e44cbf62c",
    "external_patient_id": "764145",
    "event_type": "discharge",
    "event_sequence": -1,
    "is_final_event": "Unknown",
    "resources": [
      { "file_id": "0be13f1e-ecce-4193-a300-685d42641c74", "resource_ids": ["transitions/7627990518163879710"] }
    ]
  }
}
```

## 2. HL7 ADT Alerts

**Type:** `com.particlehealth.api.v2.hl7v2`

Raw HL7 v2 ADT message notifications (legacy format).

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| message_id | string | HL7 message identifier |
| particle_patient_id | string | Particle patient UUID |
| external_patient_id | string | Customer's patient ID |

### HL7 Event Codes

| Code | Meaning |
|------|---------|
| A01 | Admission/Visit Notification |
| A03 | Discharge/End Visit |
| A04 | Register a Patient |
| A06 | Change from Outpatient to Inpatient |
| A08 | Update Patient Information |

**Subject format:** `"HL7v2 {event_code} Message for {external_patient_id}"`

### Example

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.hl7v2",
  "subject": "HL7v2 A03 Message for f8f84487-a0bb-459f-a74a-9a5ab6c1af75",
  "source": "api/notifications",
  "id": "2aba28c0-8b70-474a-9e8d-8097c63508d7",
  "time": "2026-02-04T11:20:15Z",
  "datacontenttype": "application/json",
  "data": {
    "message_id": "2aba28c0-8b70-474a-9e8d-8097c63508d7",
    "particle_patient_id": "789b6973-6ce0-4fa5-8320-57859066d12f",
    "external_patient_id": "f8f84487-a0bb-459f-a74a-9a5ab6c1af75"
  }
}
```

## 3. Query Complete

**Type:** `com.particlehealth.api.v2.query`

Fires when a patient data query completes. Covers FHIR, Deltas, and Boost query formats.

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| query_id | string | Query identifier |
| person_id | string | Legacy identifier (may be empty) |
| patient_id | string | May match person_id or particle_patient_id |
| particle_patient_id | string | Particle patient UUID (may be empty) |
| external_patient_id | string | Customer's patient ID |
| file_count | string | Number of files retrieved (**string, not number**) |
| status | string | `"COMPLETE"` |
| purpose | string | `"TREATMENT"`, `"OPERATIONS"`, or `"PAYMENT"` |

### Subject Values by Query Format

| Format | subject (success) | subject (partial errors) |
|--------|-------------------|--------------------------|
| FHIR | `"FHIR_R4 Query Complete"` | `"FHIR_R4 Query Complete with Errors. CCDA documents available"` |
| Deltas | `"DELTAS Query Complete"` | `"DELTAS Query Complete with Errors. CCDA documents available"` |
| Boost | `"BOOST_V2 Query Complete"` | `"BOOST_V2 Query Complete with Errors. CCDA documents available"` |

### Gotchas

- `file_count` is a **string**, not a number. Parse it: `parseInt(data.file_count)`.
- `particle_patient_id` may be an empty string in FHIR query notifications.
- `person_id` may be empty in Deltas/Boost notifications.

### Example (FHIR)

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.query",
  "subject": "FHIR_R4 Query Complete",
  "source": "api/notifications",
  "id": "55e82870-2ca1-4a63-b467-cd4e3ea30d14",
  "time": "2026-02-05T10:15:30Z",
  "datacontenttype": "application/json",
  "data": {
    "query_id": "55e82870-2ca1-4a63-b467-cd4e3ea30d14",
    "person_id": "2628ff9a-282f-4336-8c2f-8e08cc76141f",
    "patient_id": "2628ff9a-282f-4336-8c2f-8e08cc76141f",
    "file_count": "3",
    "status": "COMPLETE",
    "purpose": "TREATMENT",
    "particle_patient_id": "",
    "external_patient_id": "ar63uc14"
  }
}
```

## 4. New Encounter Alerts

**Type:** `com.particlehealth.api.v2.encounteralerts`

Fires when new encounter data becomes available for a monitored patient.

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| particle_patient_id | string | Particle patient UUID |
| external_patient_id | string | Customer's patient ID |
| query_id | string | Associated query ID |
| network_alert_ids | null \| string[] | Related network alert IDs |
| adt_message_ids | null \| string[] | Related ADT message IDs |
| resources | array | `[{ file_id: string, resource_ids: string[] }]` |

`resource_ids` use FHIR-style format: `"Encounter/{sha256_hash}"`.

### Example

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.encounteralerts",
  "subject": "New Encounter",
  "source": "api/notifications",
  "id": "707dfc71-eed0-4609-a824-b2f0879f443f",
  "time": "2026-02-05T12:30:45Z",
  "datacontenttype": "application/json",
  "data": {
    "particle_patient_id": "707dfc71-eed0-4609-a824-b2f0879f443f",
    "external_patient_id": "692746b562d1f442ed8fded5",
    "query_id": "b4098a67-4946-4114-aa7a-48b033ec95dd",
    "network_alert_ids": null,
    "adt_message_ids": null,
    "resources": [
      { "file_id": "", "resource_ids": ["Encounter/bc90cbe5a6ff4047adcf9a2cb990c320ecb57f756ee96e4ee0de2fb8bf12c1e5"] },
      { "file_id": "", "resource_ids": ["Encounter/c1785c04e89221ab79a900d1b12f1fc61070fed2105b926a233425001bdd4458"] }
    ]
  }
}
```

## 5. AI Outputs Complete

**Type:** `com.particlehealth.api.v2.aioutputs`

Fires when AI-generated outputs (patient summaries, clinical insights) finish processing.

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| query_id | string | Associated query ID |
| particle_patient_id | string | Particle patient UUID |
| outputs | array | `[{ ai_output_id: string, output_type: string, status: "completed" \| "failed" }]` |

Known `output_type` values: `"PATIENT_HISTORY"`.

### Example

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.aioutputs",
  "subject": "AI Outputs completed (1 completed, 0 failed)",
  "source": "api/notifications",
  "id": "e4c281cd-c5d1-4073-ba33-2dfad0b55b39",
  "time": "2026-02-05T09:20:15Z",
  "datacontenttype": "application/json",
  "data": {
    "query_id": "54c9455a-e499-4742-bb27-a7642770b37a",
    "particle_patient_id": "e4c281cd-c5d1-4073-ba33-2dfad0b55b39",
    "outputs": [
      { "ai_output_id": "16039729788028982914", "output_type": "PATIENT_HISTORY", "status": "completed" }
    ]
  }
}
```

## 6. Patient Consent Updated

**Type:** `com.particlehealth.api.v2.consent`

Fires when a patient's consent status changes for data sharing.

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| partner | string | Network partner name (e.g., `"healthix"`) |
| permission | string | `"Y"` (granted) or `"N"` (denied) |
| consent_date | string | Format: `YYYY-MM-DD` |
| particle_patient_id | string | Particle patient UUID |
| external_patient_id | string | Customer's patient ID |

### Example

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.consent",
  "subject": "Patient Consent Updated",
  "source": "api/notifications",
  "id": "04f08ed6-5984-46c1-97d1-f0e80a82a727",
  "time": "2026-02-05T11:15:00Z",
  "datacontenttype": "application/json",
  "data": {
    "partner": "healthix",
    "permission": "Y",
    "consent_date": "2025-09-25",
    "particle_patient_id": "04f08ed6-5984-46c1-97d1-f0e80a82a727",
    "external_patient_id": "140307a6-038b-4446-bdbb-7dd3f2e4a0f0"
  }
}
```

## 7. Medication Fills Data Available

**Type:** `com.particlehealth.api.v2.medicationfills`

Fires when new medication fill data becomes available (Surescripts integration).

### Data Payload

| Field | Type | Description |
|-------|------|-------------|
| particle_patient_id | string | Particle patient UUID |
| external_patient_id | string | Customer's patient ID |
| query_id | string | Associated query ID |
| count | number | Number of new medication fills |

### Example

```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.medicationfills",
  "subject": "Medication Fills Data Available",
  "source": "api/notifications",
  "id": "ea8bb001-bdbe-4635-a9e1-4e1d4a944c56",
  "time": "2026-02-05T13:45:30Z",
  "datacontenttype": "application/json",
  "data": {
    "particle_patient_id": "ea8bb001-bdbe-4635-a9e1-4e1d4a944c56",
    "external_patient_id": "1088",
    "query_id": "f1ff389f-ecb7-4345-96ad-4b264496648e",
    "count": 1
  }
}
```

## Signature Verification

All notifications are signed with HMAC SHA-256 via the `X-Ph-Signature-256` header.

**Header format:** `t={unix_timestamp},{signature}`

**Verification steps:**

1. Extract `timestamp` and `signature` from the header
2. Construct the signed payload: `{timestamp}.{raw_json_body}`
3. Generate HMAC SHA-256 using your signature key
4. Compare your generated signature with the received signature

## Resources Array

The `resources` field (in transition, encounter, and some other notifications) contains references to retrievable data:

| Field | Description |
|-------|-------------|
| `file_id` | Used with file retrieval endpoints. May be empty string. |
| `resource_ids` | FHIR-style identifiers or transition IDs (e.g., `"transitions/123"`, `"Encounter/{hash}"`) |
