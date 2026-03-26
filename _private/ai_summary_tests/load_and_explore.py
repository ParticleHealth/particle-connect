#!/usr/bin/env python3
"""Load flat_data.json into SQLite and explore AI outputs + citations.

Demonstrates:
  1. Loading all flat data into SQLite
  2. Querying AI outputs and their citations
  3. Resolving citations to source documents
  4. Measuring the citation resolution gap
  5. Building a summary → citation → source provenance chain
"""

import json
import sqlite3
import os
import sys

SAMPLE_DATA = os.path.join(
    os.path.dirname(__file__),
    "../../particle-analytics-quickstarts/sample-data/flat_data.json",
)
DB_PATH = os.path.join(os.path.dirname(__file__), "ai_summary.db")


def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def to_text(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def load_flat_data(conn, flat_data, patient_id="sample-patient"):
    """Load all resource types into SQLite tables."""
    cursor = conn.cursor()

    for resource_type, records in flat_data.items():
        if not isinstance(records, list) or not records:
            continue

        columns = set()
        for record in records:
            if isinstance(record, dict):
                columns.update(record.keys())
        if not columns:
            continue

        table_name = sanitize(resource_type)
        col_names = sorted(columns)
        safe_cols = [sanitize(c) for c in col_names]
        all_cols = ["_patient_id"] + safe_cols
        col_defs = ", ".join(f'"{c}" TEXT' for c in all_cols)

        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        placeholders = ", ".join(["?"] * len(all_cols))
        insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

        for record in records:
            if not isinstance(record, dict):
                continue
            values = [patient_id] + [to_text(record.get(c)) for c in col_names]
            cursor.execute(insert_sql, values)

        print(f"  {table_name}: {len(records)} rows")

    conn.commit()


def explore(conn):
    """Run exploration queries and print results."""
    cursor = conn.cursor()

    # --- 1. AI Output overview ---
    print("\n" + "=" * 70)
    print("1. AI OUTPUTS OVERVIEW")
    print("=" * 70)

    cursor.execute("""
        SELECT ai_output_id, type, created,
               LENGTH(text) AS text_length
        FROM aIOutputs
        ORDER BY type, created
    """)
    rows = cursor.fetchall()
    print(f"\nTotal AI outputs: {len(rows)}")
    print(f"{'ID':<25} {'Type':<20} {'Text Length':>12}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<25} {row[1]:<20} {row[3]:>12} chars")

    # --- 2. Citations per output ---
    print("\n" + "=" * 70)
    print("2. CITATIONS PER OUTPUT")
    print("=" * 70)

    cursor.execute("""
        SELECT o.ai_output_id, o.type,
               COUNT(c.citation_id) AS citation_count,
               COUNT(DISTINCT c.resource_reference_id) AS unique_sources
        FROM aIOutputs o
        LEFT JOIN aICitations c ON o.ai_output_id = c.ai_output_id
        GROUP BY o.ai_output_id, o.type
        ORDER BY citation_count DESC
    """)
    rows = cursor.fetchall()
    print(f"\n{'ID':<25} {'Type':<20} {'Citations':>10} {'Sources':>10}")
    print("-" * 68)
    for row in rows:
        print(f"{row[0]:<25} {row[1]:<20} {row[2]:>10} {row[3]:>10}")

    # --- 3. Citation resource types ---
    print("\n" + "=" * 70)
    print("3. CITATION RESOURCE TYPE DISTRIBUTION")
    print("=" * 70)

    cursor.execute("""
        SELECT resource_type, COUNT(*) AS cnt
        FROM aICitations
        GROUP BY resource_type
        ORDER BY cnt DESC
    """)
    rows = cursor.fetchall()
    total = sum(r[1] for r in rows)
    print(f"\n{'Resource Type':<25} {'Count':>8} {'%':>8}")
    print("-" * 44)
    for row in rows:
        pct = 100.0 * row[1] / total
        print(f"{row[0]:<25} {row[1]:>8} {pct:>7.1f}%")

    # --- 4. Citation resolution gap ---
    print("\n" + "=" * 70)
    print("4. CITATION RESOLUTION GAP")
    print("=" * 70)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT c.resource_reference_id) AS total_doc_refs,
            COUNT(DISTINCT CASE WHEN d.document_reference_id IS NOT NULL
                          THEN c.resource_reference_id END) AS resolved,
            COUNT(DISTINCT CASE WHEN d.document_reference_id IS NULL
                          THEN c.resource_reference_id END) AS orphaned
        FROM aICitations c
        LEFT JOIN documentReferences d
            ON c.resource_reference_id = d.document_reference_id
        WHERE c.resource_type = 'DocumentReferences'
    """)
    row = cursor.fetchone()
    print(f"\n  Total unique DocumentReference citation refs: {row[0]}")
    print(f"  Resolved (found in documentReferences table): {row[1]}")
    print(f"  Orphaned (not in flat data):                  {row[2]}")
    if row[0]:
        print(f"  Resolution rate: {100.0 * row[1] / row[0]:.1f}%")

    # --- 5. Structured citation resolution ---
    print("\n" + "=" * 70)
    print("5. STRUCTURED CITATION RESOLUTION (non-DocumentReferences)")
    print("=" * 70)

    # Labs
    cursor.execute("""
        SELECT COUNT(*) AS total,
               COUNT(DISTINCT CASE WHEN l.lab_observation_id IS NOT NULL
                             THEN c.resource_reference_id END) AS resolved
        FROM aICitations c
        LEFT JOIN labs l ON c.resource_reference_id = l.lab_observation_id
        WHERE c.resource_type = 'Labs'
    """)
    row = cursor.fetchone()
    print(f"\n  Labs: {row[1]} resolved out of {row[0]} citations")

    # Encounters
    cursor.execute("""
        SELECT COUNT(*) AS total,
               COUNT(DISTINCT CASE WHEN e.encounter_id IS NOT NULL
                             THEN c.resource_reference_id END) AS resolved
        FROM aICitations c
        LEFT JOIN encounters e ON c.resource_reference_id = e.encounter_id
        WHERE c.resource_type = 'Encounters'
    """)
    row = cursor.fetchone()
    print(f"  Encounters: {row[1]} resolved out of {row[0]} citations")

    # --- 6. Sample: Full provenance chain ---
    print("\n" + "=" * 70)
    print("6. SAMPLE PROVENANCE CHAIN (first discharge summary)")
    print("=" * 70)

    cursor.execute("""
        SELECT ai_output_id, SUBSTR(text, 1, 200) AS text_preview
        FROM aIOutputs
        WHERE type = 'DISCHARGE_SUMMARY'
        LIMIT 1
    """)
    output = cursor.fetchone()
    if output:
        oid = output[0]
        print(f"\n  Output ID: {oid}")
        print(f"  Preview: {output[1]}...")

        cursor.execute("""
            SELECT c.citation_id, c.resource_type,
                   c.resource_reference_id, c.text_snippet
            FROM aICitations c
            WHERE c.ai_output_id = ?
            LIMIT 5
        """, (oid,))
        cites = cursor.fetchall()
        for i, cite in enumerate(cites, 1):
            print(f"\n  Citation {i}:")
            print(f"    resource_type: {cite[1]}")
            print(f"    resource_ref:  {cite[2][:50]}...")
            print(f"    snippet:       {cite[3]}")

            # Try to resolve
            if cite[1] == "DocumentReferences":
                cursor.execute("""
                    SELECT document_reference_type,
                           SUBSTR(document_reference_content_data, 1, 100)
                    FROM documentReferences
                    WHERE document_reference_id = ?
                """, (cite[2],))
                doc = cursor.fetchone()
                if doc:
                    print(f"    RESOLVED → {doc[0]}: {doc[1]}...")
                else:
                    print(f"    ORPHANED — not in documentReferences table")


def main():
    print("Loading flat_data.json into SQLite...\n")

    with open(SAMPLE_DATA) as f:
        flat_data = json.load(f)

    # Remove existing DB for clean load
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    load_flat_data(conn, flat_data)
    explore(conn)
    conn.close()

    print(f"\n\nDatabase saved to: {DB_PATH}")
    print("Run queries with: sqlite3 ai_summary.db")


if __name__ == "__main__":
    main()
