"""Configuration for care coordination voice demo.

Particle credentials: reuses sandbox credentials from particle-e2e.
Voice platform: Retell AI (swap for Vapi by changing voice_client.py).

Loads .env file from this directory if present.
"""

import os
from pathlib import Path

# Load .env file if it exists (no dependency on python-dotenv)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Don't override existing env vars
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
# Your Retell phone number (outbound caller ID) — set up in Retell dashboard
RETELL_FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER", "")

# --- Demo settings ---
# For demo/testing, override the patient's phone with your own
DEMO_OVERRIDE_PHONE = os.getenv("DEMO_OVERRIDE_PHONE", "")

# Webhook URL where Retell sends call events (ngrok or deployed endpoint)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/call-events")

# --- Sandbox demo patient (same as particle-e2e) ---
DEMO_PATIENT = {
    "patient_id": "care-coord-voice-demo",
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
