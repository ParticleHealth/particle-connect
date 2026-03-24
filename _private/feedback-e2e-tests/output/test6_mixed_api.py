#!/usr/bin/env python3
"""Mixed API E2E Test: Management API + Query Flow API in a single script.

This script demonstrates a full lifecycle spanning both Particle APIs:
1. Authenticate with the Management API using org-level credentials
2. Create a new project ("test-project") via the Management API
3. Create a service account under that project
4. Generate credentials for the service account
5. Using those credentials, register a patient and run a query via the Query Flow SDK
6. Retrieve both flat data and CCDA XML for the same patient
7. Parse the CCDA XML: extract patient name, medication entries, problem entries
8. Load flat data into DuckDB and count records per table
9. Compare medications between CCDA and flat data (both directions)

Prerequisites:
    Org-level credentials in management-ui/.env (or set as environment variables):
    - PARTICLE_ORG_CLIENT_ID (or PARTICLE_CLIENT_ID in management-ui/.env)
    - PARTICLE_ORG_CLIENT_SECRET (or PARTICLE_CLIENT_SECRET in management-ui/.env)

    The particle-api-quickstarts SDK must be installed:
        cd particle-api-quickstarts && pip install -e ".[dev]"

Usage:
    cd particle-api-quickstarts
    source .venv/bin/activate
    python ../_private/feedback-e2e-tests/output/test6_mixed_api.py

Notes:
    - Management API uses POST /auth (org-level), Query Flow uses GET /auth (project-level)
    - Management API lives on management.sandbox.particlehealth.com
    - address_state MUST be a two-letter abbreviation (e.g. "MA"), never the full state name
    - FHIR returns 404 in sandbox; use flat + CCDA instead
    - Flat data only returns results for seeded test patients in sandbox
"""

import io
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import parse_qs

import duckdb
import httpx

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SANDBOX_AUTH_URL = "https://sandbox.particlehealth.com"
MANAGEMENT_BASE_URL = "https://management.sandbox.particlehealth.com"

# Sandbox seeded test patient -- the only patient that returns flat data.
DEMO_PATIENT = PatientRegistration(
    given_name="Elvira",
    family_name="Valadez-Nucleus",
    date_of_birth="1970-12-26",
    gender=Gender.FEMALE,
    postal_code="02215",
    address_city="Boston",
    address_state="MA",  # Two-letter abbreviation required
    patient_id="test6-mixed-api-e2e",
    address_lines=[""],
    ssn="123-45-6789",
    telephone="234-567-8910",
)

# CCDA XML namespace
CCDA_NS = {"hl7": "urn:hl7-org:v3"}


# ---------------------------------------------------------------------------
# Management API helpers (raw httpx -- no SDK for management)
# ---------------------------------------------------------------------------


def load_org_credentials() -> tuple[str, str]:
    """Load org-level credentials from environment or management-ui/.env."""
    client_id = os.environ.get("PARTICLE_ORG_CLIENT_ID", "")
    client_secret = os.environ.get("PARTICLE_ORG_CLIENT_SECRET", "")

    if client_id and client_secret:
        return client_id, client_secret

    # Fall back to management-ui/.env
    mgmt_env_path = Path(__file__).resolve().parents[3] / "management-ui" / ".env"
    if mgmt_env_path.exists():
        env_vars = {}
        for line in mgmt_env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env_vars[key.strip()] = value.strip()
        client_id = env_vars.get("PARTICLE_CLIENT_ID", "")
        client_secret = env_vars.get("PARTICLE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        print("ERROR: Could not find org-level credentials.")
        print("Set PARTICLE_ORG_CLIENT_ID / PARTICLE_ORG_CLIENT_SECRET,")
        print("or ensure management-ui/.env has PARTICLE_CLIENT_ID / PARTICLE_CLIENT_SECRET.")
        sys.exit(1)

    return client_id, client_secret


def management_auth(client_id: str, client_secret: str) -> str:
    """Authenticate with Management API (POST /auth, org-level).

    Returns a JWT access token.
    """
    resp = httpx.post(
        f"{SANDBOX_AUTH_URL}/auth",
        headers={"client-id": client_id, "client-secret": client_secret},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  Management auth failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    # Response may be URL-encoded form data or JSON
    try:
        data = resp.json()
    except Exception:
        parsed = parse_qs(resp.text)
        data = {k: v[0] for k, v in parsed.items()}

    token = data.get("access_token", "")
    if not token:
        print(f"  No access_token in auth response: {data}")
        sys.exit(1)

    return token


def mgmt_request(
    method: str,
    path: str,
    token: str,
    json_body: dict | None = None,
) -> dict | list:
    """Make an authenticated request to the Management API."""
    url = f"{MANAGEMENT_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.request(method, url, headers=headers, json=json_body, timeout=30)
    if resp.status_code >= 400:
        detail = resp.text
        try:
            err = resp.json()
            detail = err.get("message", err.get("error", detail))
        except Exception:
            pass
        print(f"  Management API error ({resp.status_code}) {method} {path}: {detail}")
        sys.exit(1)

    if resp.status_code == 204:
        return {}
    return resp.json()


# ---------------------------------------------------------------------------
# CCDA XML parsing helpers
# ---------------------------------------------------------------------------


def parse_ccda_patient_name(root: ET.Element) -> str:
    """Extract patient name from a CCDA XML document."""
    # recordTarget/patientRole/patient/name
    for patient in root.iter(f"{{{CCDA_NS['hl7']}}}patient"):
        name_el = patient.find("hl7:name", CCDA_NS)
        if name_el is None:
            continue
        givens = [g.text or "" for g in name_el.findall("hl7:given", CCDA_NS)]
        families = [f.text or "" for f in name_el.findall("hl7:family", CCDA_NS)]
        full_name = " ".join(givens + families).strip()
        if full_name:
            return full_name
    return "Unknown"


def parse_ccda_medications(root: ET.Element) -> list[str]:
    """Extract medication names from a CCDA XML document.

    Looks in the Medications section (templateId 2.16.840.1.113883.10.20.22.2.1
    or 2.16.840.1.113883.10.20.22.2.1.1) and in substanceAdministration entries.
    """
    meds = []

    # Strategy 1: Find medication entries via substanceAdministration
    for sa in root.iter(f"{{{CCDA_NS['hl7']}}}substanceAdministration"):
        consumable = sa.find(".//hl7:consumable//hl7:manufacturedMaterial", CCDA_NS)
        if consumable is not None:
            code_el = consumable.find("hl7:code", CCDA_NS)
            if code_el is not None:
                name = code_el.get("displayName", "")
                if name:
                    meds.append(name)
                    continue
                # Check for originalText or translation
                orig = code_el.find("hl7:originalText", CCDA_NS)
                if orig is not None and orig.text:
                    meds.append(orig.text.strip())
                    continue
                trans = code_el.find("hl7:translation", CCDA_NS)
                if trans is not None:
                    name = trans.get("displayName", "")
                    if name:
                        meds.append(name)
                        continue
            # Check name element
            name_el = consumable.find("hl7:name", CCDA_NS)
            if name_el is not None and name_el.text:
                meds.append(name_el.text.strip())

    # Strategy 2: Fall back to section text if no structured entries found
    if not meds:
        for section in root.iter(f"{{{CCDA_NS['hl7']}}}section"):
            title_el = section.find("hl7:title", CCDA_NS)
            if title_el is not None and title_el.text and "medication" in title_el.text.lower():
                # Try to get text content from table rows
                for content in section.iter(f"{{{CCDA_NS['hl7']}}}content"):
                    if content.text and content.text.strip():
                        meds.append(content.text.strip())

    return list(dict.fromkeys(meds))  # deduplicate while preserving order


def parse_ccda_problems(root: ET.Element) -> list[str]:
    """Extract problem/condition names from a CCDA XML document.

    Looks in the Problems section and observation entries with problem-type templates.
    """
    problems = []

    # Look for observations that represent problems/conditions
    for obs in root.iter(f"{{{CCDA_NS['hl7']}}}observation"):
        # Check if this is a problem observation
        for template_id in obs.findall("hl7:templateId", CCDA_NS):
            root_val = template_id.get("root", "")
            # Problem observation template IDs
            if root_val in (
                "2.16.840.1.113883.10.20.22.4.4",   # Problem observation
                "2.16.840.1.113883.10.20.22.4.38",   # Problem status
            ):
                value_el = obs.find("hl7:value", CCDA_NS)
                if value_el is not None:
                    name = value_el.get("displayName", "")
                    if name:
                        problems.append(name)
                        break
                    orig = value_el.find("hl7:originalText", CCDA_NS)
                    if orig is not None and orig.text:
                        problems.append(orig.text.strip())
                        break
                    trans = value_el.find("hl7:translation", CCDA_NS)
                    if trans is not None:
                        name = trans.get("displayName", "")
                        if name:
                            problems.append(name)
                            break
                # Check code element as fallback
                code_el = obs.find("hl7:code", CCDA_NS)
                if code_el is not None:
                    name = code_el.get("displayName", "")
                    if name and "problem" not in name.lower():
                        problems.append(name)
                break

    # Fallback: scan section titles for "Problems" / "Conditions"
    if not problems:
        for section in root.iter(f"{{{CCDA_NS['hl7']}}}section"):
            title_el = section.find("hl7:title", CCDA_NS)
            if title_el is not None and title_el.text:
                title_lower = title_el.text.lower()
                if "problem" in title_lower or "condition" in title_lower or "diagnos" in title_lower:
                    for content in section.iter(f"{{{CCDA_NS['hl7']}}}content"):
                        if content.text and content.text.strip():
                            problems.append(content.text.strip())

    return list(dict.fromkeys(problems))  # deduplicate while preserving order


# ---------------------------------------------------------------------------
# Flat data / DuckDB helpers
# ---------------------------------------------------------------------------


def _camel_to_snake(name: str) -> str:
    """Convert camelCase resource type key to snake_case table name.

    Handles Particle-specific 'aI' prefix (aICitations -> ai_citations).
    """
    if name.startswith("aI") and len(name) > 2 and name[2].isupper():
        name = "ai" + name[2:]
    result = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", result)
    return result.lower()


def load_flat_into_duckdb(conn: duckdb.DuckDBPyConnection, flat_data: dict) -> None:
    """Load flat data into DuckDB tables (all columns as TEXT)."""
    for resource_type, records in flat_data.items():
        if not isinstance(records, list) or not records:
            continue

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
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})")

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


def count_records_per_table(conn: duckdb.DuckDBPyConnection) -> list[tuple[str, int]]:
    """Return a list of (table_name, record_count) from DuckDB."""
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' ORDER BY table_name"
    ).fetchall()

    results = []
    for (table_name,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        results.append((table_name, count))
    return results


def get_flat_medications(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Get medication names from the DuckDB medications table."""
    try:
        rows = conn.execute(
            'SELECT DISTINCT "medication_name" FROM medications '
            'WHERE "medication_name" IS NOT NULL ORDER BY "medication_name"'
        ).fetchall()
        return [row[0] for row in rows]
    except duckdb.CatalogException:
        return []


def get_flat_problems(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Get problem/condition names from the DuckDB problems table."""
    try:
        rows = conn.execute(
            'SELECT DISTINCT "condition_name" FROM problems '
            'WHERE "condition_name" IS NOT NULL ORDER BY "condition_name"'
        ).fetchall()
        return [row[0] for row in rows]
    except duckdb.CatalogException:
        return []


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the full mixed API E2E test."""
    configure_logging()

    print("=" * 70)
    print("Mixed API E2E Test: Management API + Query Flow API")
    print("=" * 70)
    print()

    # ==================================================================
    # PHASE 1: Management API -- create project, service account, creds
    # ==================================================================

    print("PHASE 1: Management API Setup")
    print("-" * 40)
    print()

    # Step 1: Load org-level credentials and authenticate
    print("Step 1: Authenticating with Management API (org-level)...")
    org_client_id, org_client_secret = load_org_credentials()
    token = management_auth(org_client_id, org_client_secret)
    print("  Authenticated successfully")
    print()

    # Step 2: Create a new project
    print("Step 2: Creating project 'test-project'...")
    project_body = {
        "project": {
            "display_name": "test-project",
            "npi": "1234567890",
            "state": "STATE_ACTIVE",
            "commonwell_type": "COMMONWELL_TYPE_POSTACUTECARE",
            "address": {
                "line1": "123 Test Street",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02215",
            },
        }
    }
    project_resp = mgmt_request("POST", "/v1/projects", token, json_body=project_body)
    # Response contains a 'project' object with 'name' field like "projects/<id>"
    project_data = project_resp.get("project", project_resp)
    project_name = project_data.get("name", "")
    project_id = project_name.split("/")[-1] if "/" in project_name else project_name
    print(f"  Project created: {project_name}")
    print(f"  Project ID: {project_id}")
    print()

    # Step 3: Create a service account
    print("Step 3: Creating service account...")
    sa_body = {"service_account": {"display_name": "test-project-sa"}}
    sa_resp = mgmt_request("POST", "/v1/serviceaccounts", token, json_body=sa_body)
    sa_data = sa_resp.get("service_account", sa_resp)
    sa_name = sa_data.get("name", "")
    sa_id = sa_name.split("/")[-1] if "/" in sa_name else sa_name
    print(f"  Service account created: {sa_name}")
    print(f"  Service account ID: {sa_id}")
    print()

    # Step 4: Set IAM policy -- assign project.owner role to the service account
    print("Step 4: Setting IAM policy (project.owner)...")
    policy_body = {
        "bindings": [
            {
                "role": "project.owner",
                "resources": [f"projects/{project_id}"],
            }
        ]
    }
    mgmt_request(
        "POST",
        f"/v1/serviceaccounts/{sa_id}:setPolicy",
        token,
        json_body=policy_body,
    )
    print(f"  Policy set: project.owner on projects/{project_id}")
    print()

    # Step 5: Generate credentials for the service account
    print("Step 5: Generating credentials for service account...")
    cred_resp = mgmt_request(
        "POST",
        f"/v1/serviceaccounts/{sa_id}/credentials",
        token,
    )
    new_client_id = cred_resp.get("clientId", "")
    new_client_secret = cred_resp.get("clientSecret", "")
    if not new_client_id or not new_client_secret:
        print(f"  ERROR: No credentials returned: {cred_resp}")
        return 1
    print(f"  Client ID: {new_client_id[:12]}...")
    print("  Client Secret: ******* (captured, shown once)")
    print()

    # ==================================================================
    # PHASE 2: Query Flow API -- register patient, query, retrieve data
    # ==================================================================

    print("PHASE 2: Query Flow API (using new project credentials)")
    print("-" * 40)
    print()

    # Build settings using the new credentials
    scope_id = f"projects/{project_id}"
    os.environ["PARTICLE_CLIENT_ID"] = new_client_id
    os.environ["PARTICLE_CLIENT_SECRET"] = new_client_secret
    os.environ["PARTICLE_SCOPE_ID"] = scope_id
    os.environ["PARTICLE_BASE_URL"] = SANDBOX_AUTH_URL

    settings = ParticleSettings(
        client_id=new_client_id,
        client_secret=new_client_secret,
        scope_id=scope_id,
        base_url=SANDBOX_AUTH_URL,
    )

    print(f"  Scope: {scope_id}")
    print(f"  Base URL: {settings.base_url}")
    print()

    ccda_meds: list[str] = []
    ccda_problems: list[str] = []
    ccda_patient_name = "Unknown"
    flat_data: dict = {}

    try:
        with ParticleHTTPClient(settings) as client:
            patient_svc = PatientService(client)
            query_svc = QueryService(client)

            # Step 6: Register patient
            print("Step 6: Registering sandbox test patient...")
            response = patient_svc.register(DEMO_PATIENT)
            particle_patient_id = response.particle_patient_id
            print(f"  Particle Patient ID: {particle_patient_id}")
            print()

            # Step 7: Submit query
            print("Step 7: Submitting clinical data query...")
            query_svc.submit_query(
                particle_patient_id=particle_patient_id,
                purpose_of_use=PurposeOfUse.TREATMENT,
            )
            print("  Query submitted")
            print()

            # Step 8: Wait for completion
            print("Step 8: Waiting for query to complete (may take 2-5 minutes)...")
            result = query_svc.wait_for_query_complete(
                particle_patient_id=particle_patient_id,
                timeout_seconds=300,
            )
            print(f"  Status: {result.query_status.value}")
            if result.files_available:
                print(f"  Files available: {result.files_available}")
            print()

            # Step 9: Retrieve flat data
            print("Step 9: Retrieving flat data...")
            flat_data = query_svc.get_flat(particle_patient_id)
            print("  Resource types returned:")
            for key, value in sorted(flat_data.items()):
                if isinstance(value, list):
                    print(f"    {key}: {len(value)} records")
            print()

            # Step 10: Retrieve CCDA
            print("Step 10: Retrieving CCDA XML...")
            ccda_zip_bytes = query_svc.get_ccda(particle_patient_id)
            if not ccda_zip_bytes:
                print("  No CCDA data returned (empty response)")
            else:
                print(f"  CCDA ZIP size: {len(ccda_zip_bytes)} bytes")

                # Extract and parse CCDA XML files from the ZIP
                with zipfile.ZipFile(io.BytesIO(ccda_zip_bytes)) as zf:
                    xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
                    print(f"  XML files in ZIP: {len(xml_files)}")

                    for xml_file in xml_files:
                        print(f"\n  Parsing: {xml_file}")
                        xml_content = zf.read(xml_file)
                        try:
                            root = ET.fromstring(xml_content)
                        except ET.ParseError as e:
                            print(f"    Parse error: {e}")
                            continue

                        # Extract patient name
                        name = parse_ccda_patient_name(root)
                        if name != "Unknown":
                            ccda_patient_name = name
                        print(f"    Patient name: {name}")

                        # Extract medications
                        file_meds = parse_ccda_medications(root)
                        print(f"    Medications found: {len(file_meds)}")
                        for med in file_meds:
                            print(f"      - {med}")
                        ccda_meds.extend(file_meds)

                        # Extract problems
                        file_problems = parse_ccda_problems(root)
                        print(f"    Problems found: {len(file_problems)}")
                        for prob in file_problems:
                            print(f"      - {prob}")
                        ccda_problems.extend(file_problems)

                # Deduplicate across all files
                ccda_meds = list(dict.fromkeys(ccda_meds))
                ccda_problems = list(dict.fromkeys(ccda_problems))
            print()

    except ParticleValidationError as e:
        print(f"\nValidation error: {e.message}")
        if e.errors:
            for error in e.errors:
                print(f"  - {error}")
        return 1

    except ParticleQueryTimeoutError as e:
        print(f"\nQuery timed out: {e.message}")
        print("  The query may still be processing. Try again later.")
        return 1

    except ParticleQueryFailedError as e:
        print(f"\nQuery failed: {e.message}")
        if e.error_message:
            print(f"  Details: {e.error_message}")
        return 1

    except ParticleAPIError as e:
        print(f"\nAPI error ({e.status_code}): {e.message}")
        if e.response_body:
            print(f"  Details: {e.response_body}")
        return 1

    # ==================================================================
    # PHASE 3: DuckDB Analytics
    # ==================================================================

    print("PHASE 3: DuckDB Analytics")
    print("-" * 40)
    print()

    if not flat_data:
        print("  No flat data to load into DuckDB.")
        print("  (Sandbox only returns data for seeded test patients.)")
    else:
        conn = duckdb.connect(":memory:")

        # Load flat data into DuckDB
        print("Loading flat data into DuckDB (in-memory)...")
        load_flat_into_duckdb(conn, flat_data)
        print("  Done")
        print()

        # Count records per table
        print("Records per table:")
        print(f"  {'Table':<30} {'Records':>8}")
        print(f"  {'-' * 30} {'-' * 8}")
        table_counts = count_records_per_table(conn)
        for table_name, count in table_counts:
            print(f"  {table_name:<30} {count:>8}")
        print()

        # Get flat medications and problems for comparison
        flat_med_names = get_flat_medications(conn)
        flat_problem_names = get_flat_problems(conn)

        conn.close()

    # ==================================================================
    # PHASE 4: CCDA vs Flat Data Comparison
    # ==================================================================

    print("PHASE 4: CCDA vs Flat Data Comparison")
    print("-" * 40)
    print()

    print(f"CCDA patient name: {ccda_patient_name}")
    print()

    # Normalize names for comparison (lowercase, strip whitespace)
    def normalize(name: str) -> str:
        return name.strip().lower()

    ccda_med_set = {normalize(m) for m in ccda_meds}
    flat_med_set = {normalize(m) for m in flat_med_names} if flat_data else set()

    ccda_prob_set = {normalize(p) for p in ccda_problems}
    flat_prob_set = {normalize(p) for p in flat_problem_names} if flat_data else set()

    # Medications comparison
    print(f"Medications in CCDA: {len(ccda_meds)}")
    for m in ccda_meds:
        print(f"  - {m}")
    print()

    if flat_data:
        print(f"Medications in flat data: {len(flat_med_names)}")
        for m in flat_med_names:
            print(f"  - {m}")
        print()

        in_ccda_not_flat = ccda_med_set - flat_med_set
        in_flat_not_ccda = flat_med_set - ccda_med_set

        if in_ccda_not_flat:
            print(f"Medications in CCDA but NOT in flat data ({len(in_ccda_not_flat)}):")
            for m in sorted(in_ccda_not_flat):
                print(f"  - {m}")
        else:
            print("All CCDA medications also appear in flat data (or both are empty).")
        print()

        if in_flat_not_ccda:
            print(f"Medications in flat data but NOT in CCDA ({len(in_flat_not_ccda)}):")
            for m in sorted(in_flat_not_ccda):
                print(f"  - {m}")
        else:
            print("All flat data medications also appear in CCDA (or both are empty).")
        print()
    else:
        print("(No flat data available for medication comparison)")
        print()

    # Problems comparison
    print(f"Problems in CCDA: {len(ccda_problems)}")
    for p in ccda_problems:
        print(f"  - {p}")
    print()

    if flat_data:
        print(f"Problems in flat data: {len(flat_problem_names)}")
        for p in flat_problem_names:
            print(f"  - {p}")
        print()

        in_ccda_not_flat_p = ccda_prob_set - flat_prob_set
        in_flat_not_ccda_p = flat_prob_set - ccda_prob_set

        if in_ccda_not_flat_p:
            print(f"Problems in CCDA but NOT in flat data ({len(in_ccda_not_flat_p)}):")
            for p in sorted(in_ccda_not_flat_p):
                print(f"  - {p}")
        else:
            print("All CCDA problems also appear in flat data (or both are empty).")
        print()

        if in_flat_not_ccda_p:
            print(f"Problems in flat data but NOT in CCDA ({len(in_flat_not_ccda_p)}):")
            for p in sorted(in_flat_not_ccda_p):
                print(f"  - {p}")
        else:
            print("All flat data problems also appear in CCDA (or both are empty).")
        print()
    else:
        print("(No flat data available for problem comparison)")
        print()

    # ==================================================================
    # Summary
    # ==================================================================

    print("=" * 70)
    print("RESULT: Test completed successfully")
    print("  - Management API: project, service account, and credentials created")
    print(f"  - Query Flow API: patient registered, query completed")
    print(f"  - CCDA: {len(ccda_meds)} medication(s), {len(ccda_problems)} problem(s) extracted")
    if flat_data:
        total_records = sum(
            len(v) for v in flat_data.values() if isinstance(v, list)
        )
        print(f"  - Flat data: {total_records} total records loaded into DuckDB")
    else:
        print("  - Flat data: empty (expected for sandbox non-seeded projects)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
