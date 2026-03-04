"""Pydantic models for patient registration with Particle Health API.

This module provides validated data models for patient demographics:
- Gender: Enum for MALE/FEMALE (only values accepted by Particle API)
- PatientRegistration: Input model with field validation
- PatientResponse: Response model with Particle's patient ID

Field Format Requirements:
- date_of_birth: YYYY-MM-DD (Pydantic validates automatically)
- ssn: XXX-XX-XXXX (e.g., "123-45-6789")
- telephone: 10-digit US phone, any common format (normalized to XXX-XXX-XXXX)
- postal_code: 5-digit or 9-digit ZIP (e.g., "12345" or "12345-6789")
- address_state: Two-letter state abbreviation (e.g., "NY", not "New York")
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Gender(str, Enum):
    """Patient gender values accepted by Particle Health API.

    Note: Particle API only accepts MALE or FEMALE.
    """

    MALE = "MALE"
    FEMALE = "FEMALE"


class PatientRegistration(BaseModel):
    """Patient registration request model with validation.

    Required demographics for patient registration with Particle Health.
    Pydantic validates all fields before API submission, catching errors early.

    Attributes:
        given_name: Patient's first name (required)
        family_name: Patient's last name (required)
        date_of_birth: Birth date in YYYY-MM-DD format (required)
        gender: MALE or FEMALE (required)
        postal_code: 5 or 9 digit ZIP code (required)
        address_city: City name (required)
        address_state: Two-letter state abbreviation like "NY" (required)
        patient_id: Your external ID for idempotent registration (required)
        address_lines: Street address lines (optional)
        ssn: Social security number in XXX-XX-XXXX format (optional)
        telephone: Phone number, any common US format (normalized to XXX-XXX-XXXX)
        email: Email address (optional)
    """

    # Required fields
    given_name: str = Field(..., min_length=1, max_length=100)
    family_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    postal_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    address_city: str = Field(..., min_length=1)
    address_state: str = Field(..., min_length=1)

    # Required — API returns 400 if missing
    patient_id: str
    address_lines: list[str] | None = None
    ssn: str | None = None
    telephone: str | None = None
    email: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("ssn")
    @classmethod
    def validate_ssn(cls, v: str | None) -> str | None:
        """Validate SSN format: XXX-XX-XXXX."""
        if v is None:
            return v
        if not re.match(r"^\d{3}-\d{2}-\d{4}$", v):
            raise ValueError("SSN must be in format XXX-XX-XXXX (e.g., 123-45-6789)")
        return v

    @field_validator("telephone")
    @classmethod
    def validate_telephone(cls, v: str | None) -> str | None:
        """Validate and normalize telephone to XXX-XXX-XXXX.

        Accepts common formats like:
          234-567-8910, (234) 567-8910, 234.567.8910,
          2345678910, 1-234-567-8910, +1 234 567 8910
        """
        if v is None:
            return v
        # Strip to digits only
        digits = re.sub(r"\D", "", v)
        # Drop leading country code "1" if 11 digits
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            raise ValueError(
                "Telephone must contain 10 digits "
                "(e.g., 234-567-8910, (234) 567-8910, 2345678910)"
            )
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"


class PatientResponse(BaseModel):
    """Response model from patient registration.

    Contains the Particle-assigned patient ID plus echoed demographics.
    Uses extra="ignore" to gracefully handle unknown fields in API response.

    Attributes:
        particle_patient_id: Particle's UUID for the patient (required in response)
        All other fields from PatientRegistration
    """

    # Particle's assigned ID - required in response
    particle_patient_id: str

    # Demographics echoed back from API
    given_name: str
    family_name: str
    date_of_birth: date
    gender: Gender
    postal_code: str
    address_city: str
    address_state: str
    patient_id: str | None = None
    address_lines: list[str] | None = None
    ssn: str | None = None
    telephone: str | None = None
    email: str | None = None

    model_config = ConfigDict(extra="ignore")
