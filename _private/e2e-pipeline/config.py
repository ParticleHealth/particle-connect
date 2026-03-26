"""Sandbox configuration for Particle Health API."""

import os

SANDBOX_BASE_URL = "https://sandbox.particlehealth.com"

CLIENT_ID = os.environ["PARTICLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["PARTICLE_CLIENT_SECRET"]
SCOPE = os.environ["PARTICLE_SCOPE"]

# Database
DB_PATH = "particle_data.db"
