"""Structured logging with PHI/PII redaction for HIPAA compliance."""

from __future__ import annotations

import logging
import re
from typing import Any

import structlog

# Keys that should always be redacted (case-insensitive matching)
REDACT_KEYS: set[str] = {
    # Names
    "first_name",
    "last_name",
    "name",
    "patient_name",
    "given_name",
    "family_name",
    # Identifiers
    "ssn",
    "social_security",
    "social_security_number",
    "mrn",
    "medical_record_number",
    "patient_id",
    # Dates
    "date_of_birth",
    "dob",
    "birth_date",
    # Contact
    "address",
    "address_lines",
    "address_city",
    "street",
    "city",
    "zip",
    "postal_code",
    "phone",
    "phone_number",
    "telephone",
    "email",
    "email_address",
}

# Regex patterns for PHI that might appear in string values
PHI_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "dob": re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "mrn": re.compile(r"\b(MRN|mrn)[:\s]?\d+\b"),
}


def _redact_value(key: str, value: Any) -> Any:
    """Redact a single value if it contains PHI."""
    # Always redact known sensitive keys
    if key.lower() in REDACT_KEYS:
        return "[REDACTED]"

    # Pattern-based redaction for string values
    if isinstance(value, str):
        result = value
        for pattern_name, pattern in PHI_PATTERNS.items():
            result = pattern.sub(f"[{pattern_name.upper()}_REDACTED]", result)
        return result

    return value


def _redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact PHI from a dictionary."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _redact_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _redact_dict(v) if isinstance(v, dict) else _redact_value(key, v)
                for v in value
            ]
        else:
            result[key] = _redact_value(key, value)
    return result


def redact_phi(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor to redact PHI/PII from log output.

    This processor MUST run before any log rendering to ensure PHI
    never appears in logs, even if explicitly logged.
    """
    return _redact_dict(event_dict)


def configure_logging(
    json_output: bool = False,
    enable_redaction: bool = True,
    log_level: int = logging.INFO,
) -> None:
    """Configure structlog with PHI redaction.

    Args:
        json_output: If True, output JSON format (for production).
                    If False, use console format (for development).
        enable_redaction: If True (default), redact PHI/PII from all log output.
                         Should only be disabled for debugging in non-PHI environments.
        log_level: Minimum log level to output.
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # PHI redaction MUST come before rendering
    if enable_redaction:
        processors.append(redact_phi)

    # Output format
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Optional logger name (typically __name__ of the calling module).

    Returns:
        A bound structlog logger with PHI redaction enabled.
    """
    return structlog.get_logger(name)
