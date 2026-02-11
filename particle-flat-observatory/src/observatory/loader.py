"""PostgreSQL loader for Particle flat data.

Implements idempotent delete+insert per patient_id per resource type,
using psycopg 3 with safe dynamic SQL and transactional semantics.
"""

import logging
import os

from psycopg import sql

from observatory.schema import ResourceSchema

logger = logging.getLogger(__name__)


def get_connection_string() -> str:
    """Build a PostgreSQL connection string from environment variables.

    Reads PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE with defaults
    matching the project's compose.yaml for zero-config local development.

    Returns:
        PostgreSQL connection URI string.
    """
    host = os.environ.get("PG_HOST", "localhost")
    port = os.environ.get("PG_PORT", "5432")
    user = os.environ.get("PG_USER", "observatory")
    password = os.environ.get("PG_PASSWORD", "observatory")
    dbname = os.environ.get("PG_DATABASE", "observatory")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def load_resource(conn, table_name: str, columns: list[str], records: list[dict],
                  patient_id: str) -> int:
    """Load records for a single resource type and patient into PostgreSQL.

    Uses idempotent delete+insert within a single transaction: first deletes
    all existing rows for the patient_id, then inserts the new records.
    If the insert fails, the delete is rolled back (no data loss).

    Args:
        conn: An open psycopg connection.
        table_name: The snake_case SQL table name.
        columns: Ordered list of column names (from ResourceSchema.columns).
        records: List of record dicts to insert.
        patient_id: The patient_id to scope the delete+insert.

    Returns:
        Number of records inserted (0 if records was empty).
    """
    if not records:
        logger.debug("Skipping %s for patient %s: no records", table_name, patient_id)
        return 0

    # Build DELETE query with safe identifiers
    delete_query = sql.SQL("DELETE FROM {table} WHERE {col} = %s").format(
        table=sql.Identifier(table_name),
        col=sql.Identifier("patient_id"),
    )

    # Build INSERT query with safe identifiers for table and all columns
    col_identifiers = sql.SQL(", ").join(sql.Identifier(c) for c in columns)
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)
    insert_query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({placeholders})").format(
        table=sql.Identifier(table_name),
        columns=col_identifiers,
        placeholders=placeholders,
    )

    # Extract row tuples in column order, using .get() for missing keys (returns None)
    rows = [tuple(record.get(col) for col in columns) for record in records]

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(delete_query, (patient_id,))
            cur.executemany(insert_query, rows)

    count = len(rows)
    logger.info(
        "Loaded %d records into %s for patient %s",
        count, table_name, patient_id,
    )
    return count


def load_all(conn, data: dict[str, list[dict]],
             schemas: list[ResourceSchema]) -> dict[str, int]:
    """Load all resource types into PostgreSQL.

    Iterates over schemas (not data keys) for consistent ordering. Skips
    empty schemas (no table exists) and resource types with no records.
    Loads per-patient for idempotency: each patient_id gets its own
    delete+insert transaction per resource type.

    Args:
        conn: An open psycopg connection.
        data: Dict from load_flat_data -- resource_type -> list of record dicts.
        schemas: List of ResourceSchema objects from inspect_schema.

    Returns:
        Dict mapping table_name -> total records loaded.
    """
    results: dict[str, int] = {}

    for schema in schemas:
        if schema.is_empty:
            logger.debug("Skipping %s: empty schema (no table)", schema.table_name)
            continue

        records = data.get(schema.resource_type, [])
        if not records:
            logger.debug("Skipping %s: no records in data", schema.table_name)
            continue

        # Group records by patient_id for per-patient idempotent loading
        patients: dict[str, list[dict]] = {}
        for record in records:
            pid = record.get("patient_id", "")
            if pid not in patients:
                patients[pid] = []
            patients[pid].append(record)

        table_total = 0
        for pid, patient_records in patients.items():
            count = load_resource(
                conn=conn,
                table_name=schema.table_name,
                columns=schema.columns,
                records=patient_records,
                patient_id=pid,
            )
            table_total += count

        results[schema.table_name] = table_total

    total_tables = len(results)
    total_records = sum(results.values())
    logger.info(
        "Load complete: %d tables, %d total records",
        total_tables, total_records,
    )

    return results
