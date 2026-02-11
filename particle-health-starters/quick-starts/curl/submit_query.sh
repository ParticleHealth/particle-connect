#!/usr/bin/env bash
# Submit a clinical data query for a patient.
#
# Requires:
#   TOKEN - JWT from auth.sh (run: source quick-starts/curl/auth.sh)
#
# Usage:
#   bash quick-starts/curl/submit_query.sh <particle_patient_id>

PATIENT_ID="${1:?Usage: bash quick-starts/curl/submit_query.sh <particle_patient_id>}"
BASE_URL="${PARTICLE_BASE_URL:-https://sandbox.particlehealth.com}"

# Submit query
echo "Submitting query..."
curl -s -X POST "${BASE_URL}/api/v2/patients/${PATIENT_ID}/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "content-type: application/json" \
  -H "accept: application/json" \
  -d '{"purpose_of_use": "TREATMENT"}' | python3 -m json.tool

# Check status
echo ""
echo "Checking query status..."
curl -s "${BASE_URL}/api/v2/patients/${PATIENT_ID}/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json" | python3 -m json.tool
