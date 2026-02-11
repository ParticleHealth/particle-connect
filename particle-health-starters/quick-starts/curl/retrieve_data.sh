#!/usr/bin/env bash
# Retrieve clinical data for a patient.
#
# Requires:
#   TOKEN - JWT from auth.sh (run: source quick-starts/curl/auth.sh)
#
# Usage:
#   bash quick-starts/curl/retrieve_data.sh <particle_patient_id> [flat|fhir|ccda]

PATIENT_ID="${1:?Usage: bash quick-starts/curl/retrieve_data.sh <particle_patient_id> [flat|fhir|ccda]}"
FORMAT="${2:-flat}"
BASE_URL="${PARTICLE_BASE_URL:-https://sandbox.particlehealth.com}"

case "$FORMAT" in
  flat)
    echo "Retrieving flat data..."
    curl -s "${BASE_URL}/api/v2/patients/${PATIENT_ID}/flat" \
      -H "Authorization: Bearer $TOKEN" \
      -H "accept: application/json" | python3 -m json.tool
    ;;
  fhir)
    echo "Retrieving FHIR data..."
    curl -s "${BASE_URL}/api/v2/patients/${PATIENT_ID}/fhir" \
      -H "Authorization: Bearer $TOKEN" \
      -H "accept: application/json" | python3 -m json.tool
    ;;
  ccda)
    echo "Retrieving CCDA data..."
    curl -s "${BASE_URL}/api/v2/patients/${PATIENT_ID}/ccda" \
      -H "Authorization: Bearer $TOKEN" \
      -H "accept: application/json" \
      -o ccda_data.zip
    echo "Saved to ccda_data.zip"
    ;;
  *)
    echo "Invalid format: $FORMAT (use flat, fhir, or ccda)"
    exit 1
    ;;
esac
