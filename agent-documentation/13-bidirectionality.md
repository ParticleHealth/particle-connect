# Bi-Directionality — Documents API

Bi-directionality is the process of sending clinical data **back** to Particle Health for contribution to the health information exchange (HIE) network. While the Query Flow API retrieves data _from_ the network, the Documents API sends data _to_ the network.

## Why Bi-Directionality Matters

Health information exchange is a two-way street. When you contribute clinical documents back to Particle, those documents become available to other participants in the HIE network — improving care coordination across providers. Many network participation agreements require bi-directional data sharing.

## Documents API Overview

**Base endpoint**: `/api/v1/documents` (note: v1, not v2)

The Documents API manages clinical documents linked to patients in Particle's Master Patient Index. It supports:
- **Create/Update** — Upload CCDA XML or PDF documents
- **Retrieve** — Verify a document was uploaded successfully
- **Delete** — Remove a previously submitted document
- **List** — View all documents for a patient

**Prerequisite**: The patient must already exist in Particle's Master Patient Index (via the Patients API) before you can attach documents.

## Endpoints

### Create/Update Document
```
POST /api/v1/documents
Content-Type: multipart/form-data

Fields:
  metadata: JSON string with document metadata
  file: document file content (XML or PDF)
```

**Metadata fields**:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| patient_id | Yes | — | Your external patient ID (assigned during registration) |
| document_id | Yes | — | Your external document ID (enables idempotent re-submission) |
| type | Yes | — | Document type (typically "CLINICAL") |
| title | Yes | — | Document filename with extension (e.g., "summary.xml") |
| mime_type | Yes | — | "application/xml" or "application/pdf" |
| creation_time | Yes | — | RFC3339 timestamp (e.g., "2020-01-01T12:30:00Z") |
| format_code | Yes | — | IHE format code (e.g., "urn:ihe:pcc:xphr:2007") |
| class_code | Yes | — | LOINC document class code (e.g., "11369-6") |
| type_code | Yes | — | LOINC document type code (e.g., "11369-6") |
| confidentiality_code | No | "N" | Confidentiality level (N = Normal) |
| healthcare_facility_type_code | No | "394777002" | SNOMED facility type |
| practice_setting_code | No | "394733009" | SNOMED practice setting |
| service_start_time | No | — | Service period start (RFC3339) |
| service_stop_time | No | — | Service period end (RFC3339) |

**Example request (cURL)**:
```bash
curl -X POST "https://api.particlehealth.com/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -F 'metadata={
    "patient_id": "my-patient-001",
    "document_id": "encounter-summary-123",
    "type": "CLINICAL",
    "title": "encounter_summary.xml",
    "mime_type": "application/xml",
    "creation_time": "2020-01-01T12:30:00Z",
    "format_code": "urn:ihe:pcc:xphr:2007",
    "class_code": "11369-6",
    "type_code": "11369-6"
  }' \
  -F "file=@/path/to/document.xml"
```

**Response (200)**:
```json
{
  "patient_id": "my-patient-001",
  "document_id": "encounter-summary-123",
  "type": "CLINICAL",
  "title": "encounter_summary.xml",
  "mime_type": "application/xml",
  "creation_time": "2020-01-01T12:30:00Z",
  "format_code": "urn:ihe:pcc:xphr:2007",
  "confidentiality_code": "N",
  "class_code": "11369-6",
  "type_code": "11369-6",
  "healthcare_facility_type_code": "394777002",
  "practice_setting_code": "394733009"
}
```

### Retrieve Document
```
GET /api/v1/documents/{document_id}
```

Returns the full metadata for a previously submitted document. Use this to verify successful uploads.

**Response (200)**: Same metadata structure as the create response.

### Delete Document
```
DELETE /api/v1/documents/{document_id}
```

**Response (200)**: `"delete successful"`

### List Patient Documents
```
GET /api/v1/documents/patient/{patient_id}
```

Returns an array of all document metadata for the given patient.

**Response (200)**:
```json
[
  { "patient_id": "...", "document_id": "...", "title": "...", ... },
  { "patient_id": "...", "document_id": "...", "title": "...", ... }
]
```

## Code Value Sets

These codes describe the clinical context of uploaded documents. Networks require specific codes to properly index and route documents.

| Code | Required | Default | Description | Reference |
|------|----------|---------|-------------|-----------|
| format_code | Yes | — | Technical format (e.g., IHE XDS format) | [IHE FormatCode](https://build.fhir.org/ig/IHE/FormatCode/CodeSystem-formatcode.html) |
| class_code | Yes | — | High-level category (e.g., "11369-6" = History of Present illness) | [Document ClassCodes](https://www.hl7.org/fhir/r4/valueset-document-classcodes.html) |
| type_code | Yes | — | Precise document type (LOINC) | [Document TypeCodes](https://www.hl7.org/fhir/r4/valueset-doc-typecodes.html) |
| confidentiality_code | No | "N" | Security classification | [Confidentiality](https://terminology.hl7.org/2.1.0/CodeSystem-v3-Confidentiality.html) |
| healthcare_facility_type_code | No | "394777002" | Facility type (SNOMED) | [Facility Codes](https://www.hl7.org/fhir/valueset-c80-facilitycodes.html) |
| practice_setting_code | No | "394733009" | Clinical specialty (SNOMED) | [Practice Codes](https://www.hl7.org/fhir/valueset-c80-practice-codes.html) |

## Supported File Formats

- **C-CDA XML** (`application/xml`) — Preferred by most networks and EMRs. Standard clinical document format.
- **PDF** (`application/pdf`) — Acceptable for scanned documents, lab reports, and other non-structured content.

Networks generally request C-CDA format. Use PDF when structured XML is not available.

## Bi-Directional Data Flow

```
Your System                    Particle Health                    HIE Network
    │                               │                                │
    │── Register Patient ──────────►│                                │
    │   POST /api/v2/patients       │                                │
    │                               │                                │
    │── Submit Query ──────────────►│── Queries network ────────────►│
    │   POST /api/v2/.../query      │                                │
    │                               │◄── Clinical data returned ─────│
    │◄── Retrieve Data ─────────────│                                │
    │   GET /api/v2/.../flat|ccda   │                                │
    │                               │                                │
    │── Submit Document ───────────►│── Contributes to network ─────►│
    │   POST /api/v1/documents      │                                │
    │                               │                                │
    │── Verify Upload ─────────────►│                                │
    │   GET /api/v1/documents/{id}  │                                │
    │                               │                                │
    │── List Documents ────────────►│                                │
    │   GET /api/v1/documents/...   │                                │
```

## SDK Usage

### Submit a Document
```python
from particle.core import ParticleSettings, ParticleHTTPClient
from particle.document import DocumentService, DocumentSubmission, MimeType

settings = ParticleSettings()
with ParticleHTTPClient(settings) as client:
    service = DocumentService(client)

    document = DocumentSubmission(
        patient_id="my-patient-001",
        document_id="encounter-summary-123",
        title="encounter_summary.xml",
        mime_type=MimeType.XML,
        creation_time="2020-01-01T12:30:00Z",
        format_code="urn:ihe:pcc:xphr:2007",
        class_code="11369-6",
        type_code="11369-6",
    )

    with open("encounter_summary.xml", "rb") as f:
        response = service.submit(document, file_content=f.read())

    print(f"Submitted: {response.document_id}")
```

### Verify Upload
```python
doc = service.get("encounter-summary-123")
print(f"Title: {doc.title}, Type: {doc.mime_type}")
```

### List Patient Documents
```python
documents = service.list_by_patient("my-patient-001")
for doc in documents:
    print(f"  {doc.document_id}: {doc.title}")
```

### Delete a Document
```python
result = service.delete("encounter-summary-123")
print(result)  # "delete successful"
```

## Quick-Start Scripts

No-SDK scripts for direct API calls:

| Step | cURL | Python (httpx) |
|------|------|----------------|
| Submit Document | `quick-starts/curl/submit_document.sh` | `quick-starts/python/submit_document.py` |
| Get/Delete/List | `quick-starts/curl/manage_documents.sh` | `quick-starts/python/manage_documents.py` |

SDK workflow scripts:

| Script | Description |
|--------|-------------|
| `workflows/submit_document.py` | Submit CCDA or PDF document |
| `workflows/manage_documents.py` | Get, list, or delete documents |

## Gotchas

- **Uses v1 endpoint** — Document operations use `/api/v1/documents`, not v2
- **External patient_id** — The `patient_id` field is your external ID (from registration), NOT the Particle UUID
- **Patient must exist first** — Register the patient via POST `/api/v2/patients` before submitting documents
- **Idempotent updates** — Submitting the same `document_id` again updates the existing document
- **Delete response is JSON** — DELETE returns `{"message": "delete successful"}` (a JSON object, not a plain string)
- **List returns null when empty** — `GET /api/v1/documents/patient/{id}` returns `null` (not `[]`) when no documents exist. Always null-check before iterating.
- **Timestamps are RFC3339** — All time fields must use RFC3339 format (e.g., `2020-01-01T12:30:00Z`)
