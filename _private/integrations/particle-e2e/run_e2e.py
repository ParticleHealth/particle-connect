#!/usr/bin/env python3
"""End-to-end Particle Health integration:

  1. Authenticate with sandbox
  2. Register patient with demographics
  3. Submit query and wait for completion
  4. Retrieve CCDA data → save XML documents to disk
  5. Retrieve flat data → load into SQLite database
  6. Run SQL queries against the database

Usage:
    python run_e2e.py              # Run the full pipeline
    python run_e2e.py --queries    # Skip API calls, just run queries on existing DB
"""

import argparse
import json
import os
import sys
import zipfile
from io import BytesIO
from xml.etree import ElementTree

from particle_client import ParticleClient
from database import ParticleDatabase
from config import CCDA_OUTPUT_DIR, FLAT_DATA_FILE


# --- Sandbox demo patient ---
TEST_PATIENT = {
    "patient_id": "e2e-integration-demo",
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

CDA_NS = {"cda": "urn:hl7-org:v3"}


def save_ccda_documents(ccda_bytes: bytes):
    """Extract CCDA ZIP and save individual XML files to disk."""
    os.makedirs(CCDA_OUTPUT_DIR, exist_ok=True)

    # Save the raw ZIP
    zip_path = os.path.join(CCDA_OUTPUT_DIR, "ccda_bundle.zip")
    with open(zip_path, "wb") as f:
        f.write(ccda_bytes)
    print(f"  Saved ZIP: {zip_path} ({len(ccda_bytes):,} bytes)")

    # Extract XML files
    with zipfile.ZipFile(BytesIO(ccda_bytes)) as zf:
        xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
        print(f"  Documents in ZIP: {len(xml_files)}")

        for filename in xml_files:
            output_path = os.path.join(CCDA_OUTPUT_DIR, os.path.basename(filename))
            with zf.open(filename) as src, open(output_path, "wb") as dst:
                dst.write(src.read())

        # Print summary of each document
        for filename in xml_files:
            with zf.open(filename) as f:
                try:
                    tree = ElementTree.parse(f)
                    root = tree.getroot()

                    title_el = root.find("cda:title", CDA_NS)
                    title = title_el.text.strip() if title_el is not None and title_el.text else "Unknown"

                    time_el = root.find("cda:effectiveTime", CDA_NS)
                    date = time_el.get("value", "Unknown") if time_el is not None else "Unknown"

                    custodian_name = root.find(
                        "cda:custodian/cda:assignedCustodian/"
                        "cda:representedCustodianOrganization/cda:name",
                        CDA_NS,
                    )
                    custodian = custodian_name.text.strip() if custodian_name is not None and custodian_name.text else "Unknown"

                    print(f"    {os.path.basename(filename)}: {title} | {date} | {custodian}")
                except ElementTree.ParseError:
                    print(f"    {os.path.basename(filename)}: (could not parse)")

    print(f"  Extracted {len(xml_files)} documents to {CCDA_OUTPUT_DIR}/")


def run_pipeline():
    """Execute the full API pipeline: auth → register → query → retrieve → store."""
    client = ParticleClient()
    db = ParticleDatabase()

    try:
        # Step 1: Authenticate
        print("=" * 60)
        print("STEP 1: AUTHENTICATE")
        print("=" * 60)
        client.authenticate()
        print()

        # Step 2: Register patient
        print("=" * 60)
        print("STEP 2: REGISTER PATIENT")
        print("=" * 60)
        patient_resp = client.register_patient(TEST_PATIENT)
        patient_id = patient_resp.get("particle_patient_id")
        if not patient_id:
            print("ERROR: No patient ID returned. Full response:")
            print(json.dumps(patient_resp, indent=2))
            sys.exit(1)
        print(f"Patient ID: {patient_id}\n")

        # Step 3: Submit query and wait
        print("=" * 60)
        print("STEP 3: SUBMIT QUERY & WAIT")
        print("=" * 60)
        client.submit_query(patient_id)
        query_result = client.wait_for_query(patient_id)
        final_status = query_result.get("state", query_result.get("status", "UNKNOWN"))
        print(f"\nQuery final status: {final_status}")

        if final_status == "FAILED":
            print("Query failed. Response:")
            print(json.dumps(query_result, indent=2))
            sys.exit(1)
        print()

        # Step 4: Retrieve CCDA data → files
        print("=" * 60)
        print("STEP 4: RETRIEVE CCDA → FILES")
        print("=" * 60)
        ccda_bytes = client.get_ccda_data(patient_id)
        if ccda_bytes:
            save_ccda_documents(ccda_bytes)
        else:
            print("  No CCDA data available (some sources only return flat data).")
        print()

        # Step 5: Retrieve flat data → SQLite
        print("=" * 60)
        print("STEP 5: RETRIEVE FLAT DATA → SQLITE")
        print("=" * 60)
        flat_data = client.get_flat_data(patient_id)

        # Save raw JSON for reference
        with open(FLAT_DATA_FILE, "w") as f:
            json.dump(flat_data, f, indent=2)
        print(f"Raw flat data saved to {FLAT_DATA_FILE}\n")

        # Load into database
        print("Loading flat data into SQLite...")
        db.store_flat_data(flat_data, patient_id)
        print()

        # Show database summary
        tables = db.list_tables()
        print(f"Database tables created: {len(tables)}")
        for t in tables:
            count = db.count_rows(t)
            print(f"  {t}: {count} rows")
        print()

        return patient_id, db

    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        client.close()


def run_queries(db: ParticleDatabase, patient_id: str):
    """Run the SQL queries against the loaded database."""

    print("=" * 60)
    print("STEP 6: SQL QUERIES")
    print("=" * 60)

    query_files = [
        ("queries/patient_summary.sql", "PATIENT SUMMARY"),
        ("queries/active_problems.sql", "ACTIVE PROBLEMS"),
        ("queries/medication_list.sql", "MEDICATION LIST"),
        ("queries/lab_results.sql", "LAB RESULTS"),
        ("queries/encounter_timeline.sql", "ENCOUNTER TIMELINE"),
        ("queries/data_completeness.sql", "DATA COMPLETENESS SCORECARD"),
        ("queries/care_team.sql", "CARE TEAM"),
    ]

    for filepath, title in query_files:
        if not os.path.exists(filepath):
            print(f"\n  [SKIP] {filepath} not found")
            continue

        print(f"\n{'─' * 60}")
        print(f"  {title}")
        print(f"  Source: {filepath}")
        print(f"{'─' * 60}")

        try:
            # Read and parameterize the query
            with open(filepath) as f:
                sql = f.read()

            # Replace the placeholder patient_id with the actual one
            sql = sql.replace(":patient_id", f"'{patient_id}'")

            results = db.run_query(sql)

            if not results:
                print("  (no results)")
                continue

            # Print column headers
            columns = list(results[0].keys())
            print(f"  Columns: {', '.join(columns)}")
            print(f"  Rows: {len(results)}")
            print()

            # Print first 10 rows
            for i, row in enumerate(results[:10]):
                print(f"  Row {i + 1}:")
                for col, val in row.items():
                    if val is not None:
                        # Truncate long values for display
                        display_val = str(val)
                        if len(display_val) > 80:
                            display_val = display_val[:77] + "..."
                        print(f"    {col}: {display_val}")

            if len(results) > 10:
                print(f"\n  ... and {len(results) - 10} more rows")

        except Exception as e:
            print(f"  ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Particle Health E2E Integration")
    parser.add_argument(
        "--queries", action="store_true",
        help="Skip API calls, just run SQL queries on existing database",
    )
    parser.add_argument(
        "--patient-id", type=str, default=None,
        help="Patient ID for query mode (uses first patient in DB if not provided)",
    )
    args = parser.parse_args()

    if args.queries:
        # Query-only mode: use existing database
        db = ParticleDatabase()
        patient_id = args.patient_id
        if not patient_id:
            # Get first patient_id from any table
            tables = db.list_tables()
            for t in tables:
                rows = db.run_query(f'SELECT DISTINCT "_patient_id" FROM "{t}" LIMIT 1')
                if rows:
                    patient_id = rows[0]["_patient_id"]
                    break
        if not patient_id:
            print("ERROR: No data in database. Run without --queries first.")
            sys.exit(1)
        print(f"Using patient_id: {patient_id}\n")
        run_queries(db, patient_id)
        db.close()
    else:
        # Full pipeline
        patient_id, db = run_pipeline()
        run_queries(db, patient_id)
        db.close()

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"\nOutputs:")
    print(f"  CCDA documents: {CCDA_OUTPUT_DIR}/")
    print(f"  Flat data JSON: {FLAT_DATA_FILE}")
    print(f"  SQLite database: particle_e2e.db")
    print(f"\nRe-run queries only:")
    print(f"  python run_e2e.py --queries")


if __name__ == "__main__":
    main()
