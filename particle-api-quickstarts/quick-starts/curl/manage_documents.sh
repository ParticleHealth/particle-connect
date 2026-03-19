#!/usr/bin/env bash
# Manage documents: retrieve, delete, or list documents for a patient.
#
# Part of the bi-directional document lifecycle. After submitting a document,
# use these operations to verify, list, or remove documents.
#
# Requires:
#   TOKEN - JWT from auth.sh (run: source quick-starts/curl/auth.sh)
#
# Usage:
#   bash quick-starts/curl/manage_documents.sh get <document_id>
#   bash quick-starts/curl/manage_documents.sh delete <document_id>
#   bash quick-starts/curl/manage_documents.sh list <patient_id>

ACTION="${1:?Usage: bash quick-starts/curl/manage_documents.sh [get|delete|list] <id>}"
ID="${2:?Provide a document_id (for get/delete) or patient_id (for list)}"
BASE_URL="${PARTICLE_BASE_URL:-https://sandbox.particlehealth.com}"

case "$ACTION" in
  get)
    echo "Retrieving document: ${ID}"
    curl -s "${BASE_URL}/api/v1/documents/${ID}" \
      -H "Authorization: Bearer $TOKEN" \
      | python3 -m json.tool
    ;;
  delete)
    echo "Deleting document: ${ID}"
    curl -s -X DELETE "${BASE_URL}/api/v1/documents/${ID}" \
      -H "Authorization: Bearer $TOKEN"
    echo ""
    ;;
  list)
    echo "Listing documents for patient: ${ID}"
    curl -s "${BASE_URL}/api/v1/documents/patient/${ID}" \
      -H "Authorization: Bearer $TOKEN" \
      | python3 -m json.tool
    ;;
  *)
    echo "Invalid action: $ACTION (use get, delete, or list)"
    exit 1
    ;;
esac
