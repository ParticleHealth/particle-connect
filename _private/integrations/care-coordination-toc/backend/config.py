"""Configuration for Transitions of Care multi-agent workflow.

Particle credentials: reuses sandbox credentials from care-coordination-voice.
Voice platform: Retell AI.
Email: SMTP with console fallback.
Signal: Particle Signal ADT webhook listener.

Loads .env file from this directory if present.
"""

import os
from pathlib import Path

# Load .env file if it exists (no dependency on python-dotenv)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key not in os.environ:
                os.environ[key] = value

# --- Particle Health sandbox ---
PARTICLE_BASE_URL = os.getenv(
    "PARTICLE_BASE_URL", "https://sandbox.particlehealth.com"
)
PARTICLE_CLIENT_ID = os.environ["PARTICLE_CLIENT_ID"]
PARTICLE_CLIENT_SECRET = os.environ["PARTICLE_CLIENT_SECRET"]
PARTICLE_SCOPE = os.environ["PARTICLE_SCOPE"]

# --- Retell AI ---
RETELL_API_KEY = os.getenv("RETELL_API_KEY", "")
RETELL_BASE_URL = "https://api.retellai.com"
RETELL_FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER", "")

# --- Demo settings ---
DEMO_OVERRIDE_PHONE = os.getenv("DEMO_OVERRIDE_PHONE", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/api/webhooks/call-events")

# --- Email (SMTP with console fallback) ---
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "care-team@example.com")

# --- Signal (Particle ADT webhooks) ---
SIGNAL_WEBHOOK_SECRET = os.getenv("SIGNAL_WEBHOOK_SECRET", "")

# --- Database ---
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "toc_workflow.db"))

# --- FastAPI ---
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# --- Sandbox demo patient (same as care-coordination-voice) ---
DEMO_PATIENT = {
    "patient_id": "care-coord-toc-demo",
    "given_name": "Elvira",
    "family_name": "Valadez-Nucleus",
    "date_of_birth": "1970-12-26",
    "gender": "FEMALE",
    "postal_code": "02215",
    "address_city": "Boston",
    "address_state": "MA",
    "address_lines": [""],
    "ssn": "123-45-6789",
    "telephone": "234-567-8910",
}
