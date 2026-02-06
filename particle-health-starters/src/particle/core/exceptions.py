"""Custom exception hierarchy for Particle Health API errors."""

from __future__ import annotations


class ParticleError(Exception):
    """Base exception for all Particle Health errors."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(message)


class ParticleAuthError(ParticleError):
    """Authentication failed - invalid credentials or token issues."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="auth_error")


class ParticleAPIError(ParticleError):
    """API error response from Particle Health."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: dict | None = None,
    ):
        super().__init__(message, code="api_error")
        self.status_code = status_code
        self.response_body = response_body


class ParticleValidationError(ParticleError):
    """Request validation failed - invalid input data."""

    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message, code="validation_error")
        self.errors = errors or []


class ParticleRateLimitError(ParticleError):
    """Rate limit exceeded - too many requests."""

    def __init__(self, retry_after: int | None = None):
        message = (
            f"Rate limit exceeded. Retry after {retry_after}s"
            if retry_after
            else "Rate limit exceeded"
        )
        super().__init__(message, code="rate_limit")
        self.retry_after = retry_after


class ParticleNotFoundError(ParticleError):
    """Resource not found."""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, code="not_found")
        self.resource_type = resource_type
        self.resource_id = resource_id


class ParticleQueryTimeoutError(ParticleError):
    """Query polling timed out."""

    def __init__(self, patient_id: str, timeout_seconds: float):
        message = f"Query for patient {patient_id} timed out after {timeout_seconds}s"
        super().__init__(message, code="query_timeout")
        self.patient_id = patient_id
        self.timeout_seconds = timeout_seconds


class ParticleQueryFailedError(ParticleError):
    """Query processing failed on server."""

    def __init__(self, patient_id: str, error_message: str | None = None):
        message = f"Query for patient {patient_id} failed"
        if error_message:
            message += f": {error_message}"
        super().__init__(message, code="query_failed")
        self.patient_id = patient_id
        self.error_message = error_message
