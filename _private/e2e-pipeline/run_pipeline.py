#!/usr/bin/env python3
"""
End-to-end Particle Health pipeline:
  1. Authenticate with sandbox
  2. Register patient with demographics
  3. Submit query and wait for completion
  4. Retrieve flat data
  5. Store flat data in SQLite
  6. Query problems list
"""

import json
import sys

from particle_client import ParticleClient
from database import ParticleDatabase


# --- Sandbox demo patient (matches hello_particle.py) ---
TEST_PATIENT = {
    "patient_id": "hello-particle-demo",
    "given_name": "Elvira",
    "family_name": "Valadez-Nucleus",
    "date_of_birth": "1970-12-26",
    "gender": "FEMALE",
    "postal_code": "02215",
    "address_city": "Boston",
    "address_state": "Massachusetts",
    "address_lines": [""],
    "ssn": "123-45-6789",
    "telephone": "234-567-8910",
}


def main():
    client = ParticleClient()
    db = ParticleDatabase()

    try:
        # Step 1: Authenticate
        client.authenticate()
        print()

        # Step 2: Register patient
        patient_resp = client.register_patient(TEST_PATIENT)
        patient_id = patient_resp.get("particle_patient_id")
        if not patient_id:
            print("ERROR: No patient ID returned. Full response:")
            print(json.dumps(patient_resp, indent=2))
            sys.exit(1)
        print(f"Patient ID: {patient_id}\n")

        # Step 3: Submit query and wait
        client.submit_query(patient_id)
        query_result = client.wait_for_query(patient_id)
        final_status = query_result.get("state", query_result.get("status", "UNKNOWN"))
        print(f"\nQuery final status: {final_status}")

        if final_status == "FAILED":
            print("Query failed. Response:")
            print(json.dumps(query_result, indent=2))
            sys.exit(1)
        print()

        # Step 4: Retrieve flat data
        flat_data = client.get_flat_data(patient_id)
        print()

        # Save raw flat data for inspection
        with open("flat_data_raw.json", "w") as f:
            json.dump(flat_data, f, indent=2)
        print("Raw flat data saved to flat_data_raw.json\n")

        # Step 5: Store in SQLite
        print("Storing flat data in SQLite...")
        db.store_flat_data(flat_data, patient_id)
        print()

        # Show database summary
        tables = db.list_tables()
        print(f"Database tables created: {len(tables)}")
        for t in tables:
            count = db.count_rows(t)
            print(f"  {t}: {count} rows")
        print()

        # Step 6: Query problems list
        print("=" * 60)
        print("PROBLEMS LIST")
        print("=" * 60)
        problems = db.query_problems(patient_id)
        if problems:
            for i, problem in enumerate(problems, 1):
                print(f"\n--- Problem {i} ---")
                for key, value in problem.items():
                    if value and key != "_patient_id":
                        print(f"  {key}: {value}")
            print(f"\nTotal problems: {len(problems)}")
        else:
            print("No problems found for this patient.")

    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    main()
