#!/usr/bin/env python3
"""Example: Retrieve clinical data for a patient after query completes.

This script demonstrates:
1. Checking query status before retrieval
2. Retrieving data in different formats (FHIR, Flat, CCDA)
3. Handling each format's response (JSON vs binary)

Prerequisites:
    Set these environment variables:
    - PARTICLE_CLIENT_ID: Your Particle client ID
    - PARTICLE_CLIENT_SECRET: Your Particle client secret
    - PARTICLE_SCOPE_ID: Your Particle scope ID

    The patient must have a completed query (COMPLETE or PARTIAL status).
    Run submit_query.py first if you haven't already.

Usage:
    # Set environment variables first
    export PARTICLE_CLIENT_ID=your-client-id
    export PARTICLE_CLIENT_SECRET=your-secret
    export PARTICLE_SCOPE_ID=your-scope

    # Retrieve flat data (default)
    python workflows/retrieve_data.py <particle_patient_id>

    # Retrieve in specific format
    python workflows/retrieve_data.py <particle_patient_id> flat
    python workflows/retrieve_data.py <particle_patient_id> ccda
    python workflows/retrieve_data.py <particle_patient_id> fhir  # production only

    # Or with uv
    uv run workflows/retrieve_data.py <particle_patient_id> fhir

Formats:
    - fhir: FHIR R4 Bundle (JSON) - standard healthcare interoperability format
    - flat: Particle's flat JSON - simplified, denormalized for easy parsing
    - ccda: CCDA XML documents in a ZIP file - C-CDA standard format

Notes:
    - Uses sandbox environment by default (PARTICLE_BASE_URL)
    - CCDA format saves a ZIP file to current directory
    - FHIR and Flat formats print a summary to stdout
"""

import json
import sys

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleSettings,
    configure_logging,
)
from particle.query import QueryService, QueryStatus


def print_fhir_summary(data: dict) -> None:
    """Print a summary of FHIR Bundle contents."""
    print("\nFHIR Bundle Summary:")

    resource_type = data.get("resourceType", "Unknown")
    print(f"  Resource Type: {resource_type}")

    if "entry" in data:
        entries = data["entry"]
        print(f"  Total Entries: {len(entries)}")

        # Count resource types
        type_counts: dict[str, int] = {}
        for entry in entries:
            resource = entry.get("resource", {})
            rtype = resource.get("resourceType", "Unknown")
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        print("  Resource Types:")
        for rtype, count in sorted(type_counts.items()):
            print(f"    - {rtype}: {count}")
    else:
        print("  No entries found")


def print_flat_summary(data: dict) -> None:
    """Print a summary of Flat format contents."""
    print("\nFlat Data Summary:")

    # Count top-level keys and their sizes
    for key, value in data.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"  {key}: {len(value)} fields")
        else:
            print(f"  {key}: {type(value).__name__}")


def main() -> None:
    """Run data retrieval example."""
    # Validate command line arguments
    if len(sys.argv) < 2:
        print("Usage: python workflows/retrieve_data.py <particle_patient_id> [format]")
        print("\nFormats: flat (default), ccda, fhir (production only)")
        print("\nExample:")
        print("  python workflows/retrieve_data.py 12345678-1234-1234-1234-123456789012 fhir")
        sys.exit(1)

    particle_patient_id = sys.argv[1]
    data_format = sys.argv[2] if len(sys.argv) > 2 else "flat"

    # Validate format
    valid_formats = ["fhir", "flat", "ccda"]
    if data_format not in valid_formats:
        print(f"Invalid format: {data_format}")
        print(f"Valid formats: {', '.join(valid_formats)}")
        sys.exit(1)

    # Enable structured logging (optional, but helpful for debugging)
    configure_logging()

    # Load settings from environment variables
    settings = ParticleSettings()
    print(f"Using Particle API at: {settings.base_url}")

    try:
        with ParticleHTTPClient(settings) as client:
            service = QueryService(client)

            # Check query status first
            print(f"\nChecking query status for patient: {particle_patient_id}")
            status = service.get_query_status(particle_patient_id)
            print(f"  Status: {status.query_status.value}")

            if status.query_status not in (QueryStatus.COMPLETE, QueryStatus.PARTIAL):
                print(f"\nCannot retrieve data: query status is {status.query_status.value}")
                print("  Run submit_query.py first and wait for completion.")
                sys.exit(1)

            if status.files_available:
                print(f"  Files available: {status.files_available}")

            # Retrieve data in requested format
            print(f"\nRetrieving {data_format.upper()} data...")

            if data_format == "fhir":
                data = service.get_fhir(particle_patient_id)
                print_fhir_summary(data)
                # Save full data to file
                with open("fhir_data.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("\nFull data saved to: fhir_data.json")

            elif data_format == "flat":
                data = service.get_flat(particle_patient_id)
                print_flat_summary(data)
                # Save full data to file
                with open("flat_data.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("\nFull data saved to: flat_data.json")

            elif data_format == "ccda":
                ccda_bytes = service.get_ccda(particle_patient_id)
                if not ccda_bytes:
                    print("\nNo CCDA data available for this patient.")
                    print("  This can happen when sources only return FHIR/Flat data.")
                else:
                    filename = "ccda_data.zip"
                    with open(filename, "wb") as f:
                        f.write(ccda_bytes)
                    print(f"\nCCDA data saved to: {filename}")
                    print(f"  File size: {len(ccda_bytes):,} bytes")
                    print("\nExtract with: unzip ccda_data.zip")

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
