"""Configuration for Particle Health Bi-Directionality E2E test."""

import os

SANDBOX_BASE_URL = "https://sandbox.particlehealth.com"

CLIENT_ID = os.environ["PARTICLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["PARTICLE_CLIENT_SECRET"]
SCOPE = os.environ["PARTICLE_SCOPE"]

# Output paths
SAMPLE_DOCS_DIR = "sample-documents"
