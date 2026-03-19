#!/usr/bin/env bash
# Submit a clinical document (CCDA XML or PDF) for a patient.
#
# This is the bi-directional flow: sending clinical data BACK to Particle
# for contribution to the health information exchange network.
#
# Requires:
#   TOKEN - JWT from auth.sh (run: source quick-starts/curl/auth.sh)
#
# Usage:
#   bash quick-starts/curl/submit_document.sh <patient_id> [xml|pdf]
#
# Note: patient_id is your EXTERNAL patient ID (not the Particle UUID).

PATIENT_ID="${1:?Usage: bash quick-starts/curl/submit_document.sh <patient_id> [xml|pdf]}"
DOC_TYPE="${2:-xml}"
BASE_URL="${PARTICLE_BASE_URL:-https://sandbox.particlehealth.com}"

if [ "$DOC_TYPE" = "xml" ]; then
  echo "Submitting CCDA (XML) document for patient: ${PATIENT_ID}"

  curl -s -X POST "${BASE_URL}/api/v1/documents" \
    -H "Authorization: Bearer $TOKEN" \
    -F "metadata={
      \"patient_id\": \"${PATIENT_ID}\",
      \"document_id\": \"example-ccda-001\",
      \"type\": \"CLINICAL\",
      \"title\": \"clinical_summary.xml\",
      \"mime_type\": \"application/xml\",
      \"creation_time\": \"2020-01-01T12:30:00Z\",
      \"format_code\": \"urn:ihe:pcc:xphr:2007\",
      \"confidentiality_code\": \"N\",
      \"class_code\": \"11369-6\",
      \"type_code\": \"11369-6\",
      \"healthcare_facility_type_code\": \"394777002\",
      \"practice_setting_code\": \"394733009\",
      \"service_start_time\": \"2020-01-01T00:00:00Z\",
      \"service_stop_time\": \"2020-01-04T00:00:00Z\"
    }" \
    -F "file=@-;filename=clinical_summary.xml;type=application/xml" \
    <<< '<?xml version="1.0" encoding="UTF-8"?><ClinicalDocument xmlns="urn:hl7-org:v3"><title>Clinical Summary</title></ClinicalDocument>' \
    | python3 -m json.tool

elif [ "$DOC_TYPE" = "pdf" ]; then
  echo "Submitting PDF document for patient: ${PATIENT_ID}"

  # For real usage, replace the file path with your actual PDF:
  #   -F "file=@/path/to/your/document.pdf;type=application/pdf"
  curl -s -X POST "${BASE_URL}/api/v1/documents" \
    -H "Authorization: Bearer $TOKEN" \
    -F "metadata={
      \"patient_id\": \"${PATIENT_ID}\",
      \"document_id\": \"example-pdf-001\",
      \"type\": \"CLINICAL\",
      \"title\": \"lab_results.pdf\",
      \"mime_type\": \"application/pdf\",
      \"creation_time\": \"2020-01-01T12:30:00Z\",
      \"format_code\": \"urn:ihe:pcc:xphr:2007\",
      \"class_code\": \"11369-6\",
      \"type_code\": \"11369-6\"
    }" \
    -F "file=@/dev/null;filename=lab_results.pdf;type=application/pdf" \
    | python3 -m json.tool

else
  echo "Invalid document type: $DOC_TYPE (use xml or pdf)"
  exit 1
fi
