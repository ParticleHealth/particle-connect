"""Core infrastructure for Particle Health API client.

This module provides:
- Configuration management (ParticleSettings)
- Authentication (ParticleAuth, TokenManager)
- HTTP client with retry (ParticleHTTPClient)
- Exception hierarchy (ParticleError and subclasses)
- Structured logging with PHI redaction (configure_logging, get_logger)
"""

from .auth import ParticleAuth, TokenManager
from .config import ParticleSettings
from .exceptions import (
    ParticleAPIError,
    ParticleAuthError,
    ParticleError,
    ParticleNotFoundError,
    ParticleQueryFailedError,
    ParticleQueryTimeoutError,
    ParticleRateLimitError,
    ParticleValidationError,
)
from .http import ParticleHTTPClient
from .logging import configure_logging, get_logger, redact_phi

__all__ = [
    # Config
    "ParticleSettings",
    # Auth
    "ParticleAuth",
    "TokenManager",
    # HTTP
    "ParticleHTTPClient",
    # Exceptions
    "ParticleError",
    "ParticleAuthError",
    "ParticleAPIError",
    "ParticleValidationError",
    "ParticleRateLimitError",
    "ParticleNotFoundError",
    "ParticleQueryTimeoutError",
    "ParticleQueryFailedError",
    # Logging
    "configure_logging",
    "get_logger",
    "redact_phi",
]
