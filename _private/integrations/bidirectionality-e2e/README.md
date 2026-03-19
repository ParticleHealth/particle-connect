# Bi-Directionality E2E Test

End-to-end test for Particle Health's Documents API — the bi-directional flow where clinical data (CCDA XML and PDF) is sent **back** to Particle for contribution to the health information exchange network.

## What it tests

1. **Authenticates** with the Particle sandbox API
2. **Registers** a demo patient (Elvira Valadez-Nucleus)
3. **Submits an XML (CCDA) document** for that patient via multipart upload
4. **Submits a PDF document** for that patient via multipart upload
5. **Verifies both documents** via GET (confirms metadata round-trips correctly)
6. **Lists all documents** for the patient (confirms both appear)
7. **Deletes both documents** and verifies they're gone

## Prerequisites

```bash
pip install httpx
```

## Usage

```bash
cd _private/integrations/bidirectionality-e2e

# Full pipeline: register → submit XML → submit PDF → verify → list → delete
python run_e2e.py

# Keep documents after test (skip cleanup/deletion step)
python run_e2e.py --skip-cleanup
```

## Expected output

```
STEP 1: AUTHENTICATE
  [+] Authentication

STEP 2: REGISTER PATIENT
  [+] Patient Registration — ID: <uuid>

STEP 3: SUBMIT XML (CCDA) DOCUMENT
  [+] XML Document Submission

STEP 4: SUBMIT PDF DOCUMENT
  [+] PDF Document Submission

STEP 5: VERIFY XML DOCUMENT (GET)
  [+] XML Document Verification — document_id=bidir-e2e-ccda-001

STEP 6: VERIFY PDF DOCUMENT (GET)
  [+] PDF Document Verification — document_id=bidir-e2e-pdf-001

STEP 7: LIST PATIENT DOCUMENTS
  [+] List Patient Documents — 2 documents

STEP 8: CLEANUP (DELETE DOCUMENTS)
  [+] Delete XML Document
  [+] Delete PDF Document
  [+] Verify Deletion

TEST SUMMARY
  10/10 passed — ALL PASSED
```

## File structure

```
bidirectionality-e2e/
├── run_e2e.py                      # Main E2E test pipeline
├── particle_client.py              # API client (auth, register, documents CRUD)
├── config.py                       # Sandbox credentials and paths
├── sample-documents/
│   └── clinical_summary.xml        # Sample CCDA document for upload
└── README.md
```

## Document metadata

Both documents use metadata fields required by the Documents API:

| Field | XML Document | PDF Document |
|-------|-------------|--------------|
| document_id | bidir-e2e-ccda-001 | bidir-e2e-pdf-001 |
| type | CLINICAL | CLINICAL |
| mime_type | application/xml | application/pdf |
| format_code | urn:ihe:pcc:xphr:2007 | urn:ihe:pcc:xphr:2007 |
| class_code | 11369-6 | 11369-6 |
| type_code | 11369-6 | 11369-6 |
| confidentiality_code | N | N |

## API endpoints exercised

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/auth` | Authentication |
| POST | `/api/v2/patients` | Register patient |
| POST | `/api/v1/documents` | Submit document (multipart) |
| GET | `/api/v1/documents/{id}` | Retrieve document metadata |
| GET | `/api/v1/documents/patient/{id}` | List patient documents |
| DELETE | `/api/v1/documents/{id}` | Delete document |
