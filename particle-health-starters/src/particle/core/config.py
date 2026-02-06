"""Configuration management using pydantic-settings."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ParticleSettings(BaseSettings):
    """Configuration for Particle Health API client.

    All settings can be configured via environment variables with PARTICLE_ prefix:
        - PARTICLE_CLIENT_ID
        - PARTICLE_CLIENT_SECRET
        - PARTICLE_SCOPE_ID
        - PARTICLE_BASE_URL (optional, defaults to sandbox)
        - PARTICLE_TIMEOUT (optional, defaults to 30.0)
    """

    client_id: str = Field(..., description="Particle API client ID")
    client_secret: SecretStr = Field(..., description="Particle API client secret")
    scope_id: str = Field(..., description="Particle scope/project ID")

    # Default to sandbox for safety - production requires explicit override
    base_url: str = Field(
        default="https://sandbox.particlehealth.com",
        description="API base URL (sandbox or production)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    # Token TTL is 1 hour, refresh buffer is 10 minutes before expiry
    token_refresh_buffer_seconds: int = Field(
        default=600,
        description="Seconds before token expiry to trigger refresh",
    )

    model_config = SettingsConfigDict(
        env_prefix="PARTICLE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
