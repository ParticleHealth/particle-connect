"""Configuration for Particle Health E2E integration."""

SANDBOX_BASE_URL = "https://sandbox.particlehealth.com"

CLIENT_ID = "e9837a09-8a0c-4ad4-8653-d21a18f25898"
CLIENT_SECRET = (
    "f9f4b8496672e2b17c4bb03cb2e7e57aa88d6d38ecba73200894b23d770acb22"
    "2cfafbb20e9dbf895a79ba67f405671a41f7985fdc99487b06319b1e7dde8191"
)
SCOPE = "projects/090840b6-37d1-4cf3-936b-9e34f0543435"

# Output paths
DB_PATH = "particle_e2e.db"
CCDA_OUTPUT_DIR = "ccda_documents"
FLAT_DATA_FILE = "flat_data.json"
