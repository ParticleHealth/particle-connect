"""DuckDB loader for Particle flat data.

Implements idempotent delete+insert per patient_id per resource type,
using DuckDB with transactional semantics. Tables are auto-created
on first load via ensure_table().
"""

import logging
import os

import duckdb

from observatory.schema import ResourceSchema

logger = logging.getLogger(__name__)


def get_connection(path: str | None = None) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection.

    Args:
        path: Path to the DuckDB database file. Defaults to DUCKDB_PATH
              env var or "observatory.duckdb" in the current directory.

    Returns:
        An open DuckDB connection.
    """
    if path is None:
        path = os.environ.get("DUCKDB_PATH", "observatory.duckdb")
    return duckdb.connect(path)


def ensure_table(conn: duckdb.DuckDBPyConnection, schema: ResourceSchema) -> None:
    """Create a table if it does not already exist.

    All columns are TEXT (ELT approach). Uses double-quoted identifiers
    for column names to handle SQL reserved words.

    Args:
        conn: An open DuckDB connection.
        schema: ResourceSchema describing the table's columns.
    """
    col_defs = ", ".join(f'"{col}" TEXT' for col in schema.columns)
    sql = f'CREATE TABLE IF NOT EXISTS {schema.table_name} ({col_defs})'
    conn.execute(sql)


def load_resource(conn: duckdb.DuckDBPyConnection, table_name: str,
                  columns: list[str], records: list[dict],
                  patient_id: str) -> int:
    """Load records for a single resource type and patient into DuckDB.

    Uses idempotent delete+insert within a single transaction: first deletes
    all existing rows for the patient_id, then inserts the new records.
    If the insert fails, the delete is rolled back (no data loss).

    Args:
        conn: An open DuckDB connection.
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

    # Build column references with double-quoted identifiers
    quoted_cols = ", ".join(f'"{col}"' for col in columns)
    placeholders = ", ".join("?" for _ in columns)

    delete_sql = f'DELETE FROM {table_name} WHERE "patient_id" = ?'
    insert_sql = f'INSERT INTO {table_name} ({quoted_cols}) VALUES ({placeholders})'

    # Extract row tuples in column order, using .get() for missing keys (returns None)
    rows = [tuple(record.get(col) for col in columns) for record in records]

    conn.begin()
    try:
        conn.execute(delete_sql, [patient_id])
        conn.executemany(insert_sql, rows)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    count = len(rows)
    logger.info(
        "Loaded %d records into %s for patient %s",
        count, table_name, patient_id,
    )
    return count


def load_all(conn: duckdb.DuckDBPyConnection, data: dict[str, list[dict]],
             schemas: list[ResourceSchema]) -> dict[str, int]:
    """Load all resource types into DuckDB.

    Iterates over schemas (not data keys) for consistent ordering. Skips
    empty schemas (no table exists) and resource types with no records.
    Auto-creates tables via ensure_table() before loading.
    Loads per-patient for idempotency: each patient_id gets its own
    delete+insert transaction per resource type.

    Args:
        conn: An open DuckDB connection.
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

        # Auto-create table if it doesn't exist
        ensure_table(conn, schema)

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
