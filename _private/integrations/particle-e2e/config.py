"""Configuration for Particle Health E2E integration."""

import os

SANDBOX_BASE_URL = "https://sandbox.particlehealth.com"

CLIENT_ID = os.environ["PARTICLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["PARTICLE_CLIENT_SECRET"]
SCOPE = os.environ["PARTICLE_SCOPE"]

# Output paths
DB_PATH = "particle_e2e.db"
CCDA_OUTPUT_DIR = "ccda_documents"
FLAT_DATA_FILE = "flat_data.json"
