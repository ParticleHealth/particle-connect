"""Particle Signal webhook parsing for ADT discharge events.

Parses CloudEvents 1.0 payloads from Particle Signal and extracts
patient demographics for automatic ToC workflow creation.
"""

import hashlib
import hmac
import json
import logging

from config import SIGNAL_WEBHOOK_SECRET

logger = logging.getLogger(__name__)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature on incoming Signal webhook."""
    if not SIGNAL_WEBHOOK_SECRET:
        logger.warning("SIGNAL_WEBHOOK_SECRET not set — skipping signature verification")
        return True
    expected = hmac.new(
        SIGNAL_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_signal_event(payload: dict) -> dict | None:
    """Parse a Particle Signal CloudEvents 1.0 payload.

    Returns extracted patient info if it's a discharge event, None otherwise.
    """
    event_type = payload.get("type", "")
    data = payload.get("data", {})

    # Only process discharge events
    alert_type = data.get("alert_type", "")
    event_action = data.get("event_type", "")

    if "discharge" not in alert_type.lower() and "discharge" not in event_action.lower():
        logger.info("Ignoring non-discharge Signal event: %s / %s", alert_type, event_action)
        return None

    patient_id = data.get("patient_id", "")
    if not patient_id:
        logger.warning("Signal event missing patient_id")
        return None

    return {
        "particle_patient_id": patient_id,
        "alert_type": alert_type,
        "event_type": event_action,
        "facility_name": data.get("facility_name", ""),
        "event_date": data.get("event_date", ""),
        "raw_payload": payload,
    }
