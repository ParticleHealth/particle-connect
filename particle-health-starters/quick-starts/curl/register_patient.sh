#!/usr/bin/env bash
# Register a patient with Particle Health API.
#
# Requires:
#   TOKEN - JWT from auth.sh (run: source quick-starts/curl/auth.sh)
#
# Usage:
#   bash quick-starts/curl/register_patient.sh

BASE_URL="${PARTICLE_BASE_URL:-https://sandbox.particlehealth.com}"

curl -s -X POST "${BASE_URL}/api/v2/patients" \
  -H "Authorization: Bearer $TOKEN" \
  -H "content-type: application/json" \
  -H "accept: application/json" \
  -d '{
    "given_name": "Kam",
    "family_name": "Quark",
    "date_of_birth": "1954-12-01",
    "gender": "MALE",
    "postal_code": "11111",
    "address_city": "Brooklyn",
    "address_state": "New York",
    "address_lines": ["999 Dev Drive"],
    "ssn": "123-45-6789",
    "telephone": "234-567-8910",
    "patient_id": "my-external-id"
  }' | python3 -m json.tool
