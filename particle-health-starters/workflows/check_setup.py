#!/usr/bin/env python3
"""Validate Particle Health API environment setup.

This script checks:
1. Required environment variables are set (via ParticleSettings)
2. Credentials authenticate successfully (via ParticleHTTPClient)

Usage:
    # Set environment variables or create .env file first
    cp .env.example .env
    # Edit .env with your credentials

    python workflows/check_setup.py
"""

from pydantic import ValidationError

from particle.core import (
    ParticleAuthError,
    ParticleHTTPClient,
    ParticleSettings,
)


def main() -> None:
    """Validate environment setup."""
    print("Checking Particle Health API setup...\n")

    # Step 1: Load settings from environment
    print("1. Checking environment variables...")
    try:
        settings = ParticleSettings()
    except ValidationError as e:
        print("   FAILED: Missing required environment variables\n")
        for error in e.errors():
            field = error["loc"][0] if error["loc"] else "unknown"
            env_var = f"PARTICLE_{field}".upper()
            print(f"   - {env_var} is not set")
        print("\n   Set these variables or copy .env.example to .env:")
        print("     cp .env.example .env")
        return

    print("   OK: All required variables found")
    print(f"   - Client ID: {settings.client_id[:8]}...")
    print(f"   - Scope ID: {settings.scope_id}")
    print(f"   - Base URL: {settings.base_url}")

    # Step 2: Test authentication
    print("\n2. Testing authentication...")
    try:
        with ParticleHTTPClient(settings) as client:
            # The client authenticates on first request via ParticleAuth.
            # Make a lightweight request to trigger auth flow.
            # A 404 is fine — it means auth succeeded but patient doesn't exist.
            try:
                client.request("GET", "/api/v2/patients/setup-check/query")
            except ParticleAuthError:
                raise
            except Exception:
                # Non-auth errors (404, etc.) mean auth succeeded
                pass

            print("   OK: Authentication successful")

    except ParticleAuthError as e:
        print(f"   FAILED: {e.message}")
        print("\n   Check that your PARTICLE_CLIENT_ID and PARTICLE_CLIENT_SECRET are correct.")
        return

    # Summary
    env_type = "production" if "api.particlehealth.com" in settings.base_url else "sandbox"
    print("\n--- Setup OK ---")
    print(f"Environment: {env_type}")
    print(f"Base URL:    {settings.base_url}")
    print(f"Scope:       {settings.scope_id}")
    print("\nYou're ready to go! Try:")
    print("  python workflows/hello_particle.py")


if __name__ == "__main__":
    main()
