#!/usr/bin/env bash
# Get a JWT auth token from Particle Health API.
#
# Requires:
#   PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID
#
# Usage:
#   source quick-starts/curl/auth.sh
#   echo $TOKEN

BASE_URL="${PARTICLE_BASE_URL:-https://sandbox.particlehealth.com}"

TOKEN=$(curl -s "${BASE_URL}/auth" \
  -H "client-id: $PARTICLE_CLIENT_ID" \
  -H "client-secret: $PARTICLE_CLIENT_SECRET" \
  -H "scope: $PARTICLE_SCOPE_ID" \
  -H "accept: text/plain")

echo "Token: ${TOKEN:0:20}..."
