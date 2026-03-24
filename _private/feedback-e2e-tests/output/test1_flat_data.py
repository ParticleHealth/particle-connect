#!/usr/bin/env python3
"""Flat Data E2E Test: Register, query, retrieve, and analyze with DuckDB.

This script demonstrates the full Particle Health query-to-analytics workflow:
1. Authenticate with the Particle sandbox API (via SDK)
2. Register the sandbox test patient (Elvira Valadez-Nucleus)
3. Submit a clinical data query and wait for completion with exponential backoff
4. Retrieve flat JSON data
5. Load the flat data into DuckDB
6. Run 3 analytical queries:
   - Count of records per clinical table
   - All active medications with drug name and status
   - Most recent encounter with facility name and date

Prerequisites:
    Set these environment variables (or create a .env file in particle-api-quickstarts/):
    - PARTICLE_CLIENT_ID
    - PARTICLE_CLIENT_SECRET
    - PARTICLE_SCOPE_ID

Usage:
    cd particle-api-quickstarts
    source .venv/bin/activate
    python ../_private/feedback-e2e-tests/output/test1_flat_data.py
"""

import json
import sys
from pathlib import Path

import duckdb

from particle.core import (
    ParticleAPIError,
    ParticleHTTPClient,
    ParticleQueryFailedError,
    ParticleQueryTimeoutError,
    ParticleSettings,
    ParticleValidationError,
    configure_logging,
)
from particle.patient import Gender, PatientRegistration, PatientService
from particle.query import PurposeOfUse, QueryService

# Sandbox test patient — the only patient that returns flat data in sandbox.
# Demographics from hello_particle.py and SDK documentation.
DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",  # Two-letter abbreviation required
    patient_id="test1-flat-data-e2e",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)

# DuckDB database path (in-memory for this test, no file left behind)
DUCKDB_PATH = ":memory:"


def retrieve_flat_data(settings: ParticleSettings) -> dict:
    """Authenticate, register patient, submit query, poll, and retrieve flat data."""
    print("=== Particle Flat Data Retrieval ===\n")
    print(f"API: {settings.base_url}\n")

    with ParticleHTTPClient(settings) as client:
        patient_svc = PatientService(client)
        query_svc = QueryService(client)

        # Step 1: Register patient
        print("1. Registering sandbox test patient...")
        response = patient_svc.register(DEMO_PATIENT)
        particle_patient_id = response.particle_patient_id
        print(f"   Particle Patient ID: {particle_patient_id}")

        # Step 2: Submit query
        print("\n2. Submitting clinical data query...")
        query_svc.submit_query(
            particle_patient_id=particle_patient_id,
            purpose_of_use=PurposeOfUse.TREATMENT,
        )
        print("   Query submitted")

        # Step 3: Wait for completion (SDK uses exponential backoff automatically)
        print("\n3. Waiting for query to complete (may take 2-5 minutes)...")
        result = query_svc.wait_for_query_complete(
            particle_patient_id=particle_patient_id,
            timeout_seconds=300,
        )
        print(f"   Status: {result.query_status.value}")
        if result.files_available:
            print(f"   Files available: {result.files_available}")

        # Step 4: Retrieve flat data (not FHIR — FHIR returns 404 in sandbox)
        print("\n4. Retrieving flat JSON data...")
        flat_data = query_svc.get_flat(particle_patient_id)

        # Print summary
        print("\n   Resource types returned:")
        for key, value in sorted(flat_data.items()):
            if isinstance(value, list):
                print(f"     {key}: {len(value)} records")

        return flat_data


def load_into_duckdb(conn: duckdb.DuckDBPyConnection, flat_data: dict) -> None:
    """Load flat data into DuckDB tables (all columns as TEXT, ELT approach)."""
    print("\n=== Loading into DuckDB ===\n")

    for resource_type, records in flat_data.items():
        if not isinstance(records, list) or not records:
            continue

        # Convert camelCase to snake_case for table name
        table_name = _camel_to_snake(resource_type)

        # Discover all columns across all records
        seen_columns: dict[str, None] = {}
        for record in records:
            for key in record:
                if key not in seen_columns:
                    seen_columns[key] = None
        columns = list(seen_columns.keys())

        # Create table (all TEXT columns)
        col_defs = ", ".join(f'"{col}" TEXT' for col in columns)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})')

        # Insert records
        quoted_cols = ", ".join(f'"{col}"' for col in columns)
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = f"INSERT INTO {table_name} ({quoted_cols}) VALUES ({placeholders})"

        rows = []
        for record in records:
            row = tuple(
                str(record[col]) if record.get(col) not in (None, "") else None
                for col in columns
            )
            rows.append(row)

        conn.executemany(insert_sql, rows)
        print(f"  Loaded {len(rows)} records into {table_name}")


def _camel_to_snake(name: str) -> str:
    """Convert camelCase resource type key to snake_case table name.

    Handles Particle-specific 'aI' prefix (aICitations -> ai_citations).
    """
    import re

    # Special-case: leading "aI" prefix
    if name.startswith("aI") and len(name) > 2 and name[2].isupper():
        name = "ai" + name[2:]

    result = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", result)
    return result.lower()


def run_analytics(conn: duckdb.DuckDBPyConnection) -> None:
    """Run 3 analytical queries against the loaded DuckDB tables."""
    print("\n=== DuckDB Analytics ===\n")

    # Query 1: Count of records per clinical table
    print("--- Query 1: Record counts per clinical table ---\n")
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
    ).fetchall()

    print(f"  {'Table':<25} {'Records':>8}")
    print(f"  {'-' * 25} {'-' * 8}")
    for (table_name,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name:<25} {count:>8}")

    # Query 2: All active medications with drug name and status
    print("\n--- Query 2: Active medications (drug name + status) ---\n")
    try:
        meds = conn.execute("""
            SELECT
                "medication_name",
                "medication_statement_status",
                "medication_statement_dose_route",
                "medication_statement_dose_value",
                "medication_statement_dose_unit"
            FROM medications
            WHERE "medication_statement_status" = 'active'
               OR "medication_statement_status" IS NULL
            ORDER BY "medication_name"
        """).fetchall()

        if meds:
            print(f"  {'Medication Name':<50} {'Status':<12} {'Route':<15}")
            print(f"  {'-' * 50} {'-' * 12} {'-' * 15}")
            for med in meds:
                name = (med[0] or "Unknown")[:50]
                status = med[1] or "N/A"
                route = med[2] or ""
                print(f"  {name:<50} {status:<12} {route:<15}")
        else:
            # If no active meds, show all medications
            print("  No active medications found. Showing all medications:\n")
            all_meds = conn.execute("""
                SELECT
                    "medication_name",
                    "medication_statement_status"
                FROM medications
                ORDER BY "medication_name"
            """).fetchall()
            print(f"  {'Medication Name':<50} {'Status':<12}")
            print(f"  {'-' * 50} {'-' * 12}")
            for med in all_meds:
                name = (med[0] or "Unknown")[:50]
                status = med[1] or "N/A"
                print(f"  {name:<50} {status:<12}")
    except duckdb.CatalogException:
        print("  No medications table found in the data.")

    # Query 3: Most recent encounter with facility name and date
    print("\n--- Query 3: Most recent encounter (facility + date) ---\n")
    try:
        # Join encounters with locations via location_id_references
        # location_id_references may contain comma-delimited IDs
        encounter = conn.execute("""
            SELECT
                e."encounter_type_name",
                e."encounter_start_time" AS start_time,
                e."encounter_end_time" AS end_time,
                e."hospitalization_discharge_disposition",
                l."location_name"
            FROM encounters e
            LEFT JOIN locations l
                ON e."location_id_references" IS NOT NULL
               AND e."location_id_references" != ''
               AND l."location_id" = SPLIT_PART(e."location_id_references", ',', 1)
            WHERE e."encounter_start_time" IS NOT NULL
            ORDER BY e."encounter_start_time" DESC
            LIMIT 1
        """).fetchone()

        if encounter:
            enc_type = encounter[0] or "Unknown"
            start = encounter[1] or "N/A"
            end = encounter[2] or "N/A"
            disposition = encounter[3] or "N/A"
            facility = encounter[4] or "No facility linked"
            print(f"  Encounter Type:  {enc_type}")
            print(f"  Start Time:      {start}")
            print(f"  End Time:        {end}")
            print(f"  Facility:        {facility}")
            print(f"  Discharge:       {disposition}")
        else:
            print("  No encounters with dates found.")
    except duckdb.CatalogException:
        print("  No encounters table found in the data.")


def main() -> None:
    """Run the full flat data E2E test."""
    configure_logging()

    try:
        # Phase 1: Retrieve flat data from Particle sandbox
        settings = ParticleSettings()
        flat_data = retrieve_flat_data(settings)

        if not flat_data:
            print("\nNo flat data returned. Sandbox only returns data for seeded test patients.")
            sys.exit(1)

        # Phase 2: Load into DuckDB (in-memory)
        conn = duckdb.connect(DUCKDB_PATH)
        load_into_duckdb(conn, flat_data)

        # Phase 3: Run analytics
        run_analytics(conn)

        conn.close()
        print("\n=== Done! ===")

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")
        sys.exit(1)

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query may still be processing. Try again later.")
        sys.exit(1)

    except ParticleQueryFailedError as e:
        print(f"\nQuery failed: {e.message}")
        if e.error_message:
            print(f"  Details: {e.error_message}")
        sys.exit(1)

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
