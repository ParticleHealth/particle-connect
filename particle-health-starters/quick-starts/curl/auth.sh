#!/usr/bin/env bash
# Get a JWT auth token from Particle Health API.
#
# Requires:
#   PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID
#
# Usage:
#   source quick-starts/curl/auth.sh
#   echo $TOKEN

TOKEN=$(curl -s "https://sandbox.particlehealth.com/auth" \
  -H "client-id: $PARTICLE_CLIENT_ID" \
  -H "client-secret: $PARTICLE_CLIENT_SECRET" \
  -H "scope: $PARTICLE_SCOPE_ID" \
  -H "accept: text/plain")

echo "Token: ${TOKEN:0:20}..."
