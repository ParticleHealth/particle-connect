"""DDL generation for Particle flat data observatory.

Produces CREATE TABLE SQL for PostgreSQL and BigQuery from ResourceSchema objects.
All columns use a single type (TEXT for PostgreSQL, STRING for BigQuery) following
the ELT approach where type casting happens in queries, not on load.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from observatory.schema import ResourceSchema

logger = logging.getLogger(__name__)


class DDLDialect(str, Enum):
    """Supported SQL dialects for DDL generation."""

    POSTGRES = "postgres"
    BIGQUERY = "bigquery"


# Every column gets the same type per dialect (ELT approach).
TYPE_MAP: dict[str, str] = {
    "postgres": "TEXT",
    "bigquery": "STRING",
}

# Column name quoting per dialect.
_QUOTE_MAP: dict[str, tuple[str, str]] = {
    "postgres": ('"', '"'),
    "bigquery": ("`", "`"),
}


def _quote_column(column: str, dialect: str) -> str:
    """Quote a column name using the dialect-appropriate quoting characters."""
    left, right = _QUOTE_MAP[dialect]
    return f"{left}{column}{right}"


def generate_create_table(schema: ResourceSchema, dialect: str) -> str:
    """Generate a CREATE TABLE statement for a single resource type.

    Args:
        schema: ResourceSchema describing the table's columns.
        dialect: "postgres" or "bigquery".

    Returns:
        SQL string with CREATE TABLE (or commented-out placeholder for empty schemas).
    """
    col_type = TYPE_MAP[dialect]

    if schema.is_empty:
        return (
            f"-- Table: {schema.table_name}\n"
            f"-- No records found in sample data. Columns unknown.\n"
            f"-- Add columns manually when data becomes available.\n"
            f"-- CREATE TABLE {schema.table_name} ();"
        )

    lines = []
    lines.append(f"-- {schema.table_name}: {schema.record_count} records, "
                 f"{len(schema.columns)} columns")
    lines.append(f"CREATE TABLE IF NOT EXISTS {schema.table_name} (")

    col_lines = []
    for col in schema.columns:
        quoted = _quote_column(col, dialect)
        col_lines.append(f"  {quoted} {col_type}")

    lines.append(",\n".join(col_lines))
    lines.append(");")

    return "\n".join(lines)


def generate_ddl(schemas: list[ResourceSchema], dialect: str) -> str:
    """Generate a complete DDL file with CREATE TABLE statements for all resource types.

    Args:
        schemas: List of ResourceSchema objects (one per resource type).
        dialect: "postgres" or "bigquery".

    Returns:
        Complete SQL string with header comment and all CREATE TABLE statements.
    """
    col_type = TYPE_MAP[dialect]
    non_empty = sum(1 for s in schemas if not s.is_empty)
    empty = sum(1 for s in schemas if s.is_empty)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = (
        f"-- Particle Flat Data Observatory\n"
        f"-- DDL for {dialect} — Generated from sample data\n"
        f"-- All columns are {col_type} (ELT approach: transform in queries, not on load)\n"
        f"--\n"
        f"-- Resource types: {len(schemas)} total, {non_empty} with data, {empty} empty\n"
        f"-- Generated: {timestamp}"
    )

    table_blocks = [generate_create_table(s, dialect) for s in schemas]

    return header + "\n\n" + "\n\n".join(table_blocks) + "\n"


def write_ddl(sql: str, output_path: str | Path) -> None:
    """Write generated DDL SQL to a file, creating parent directories as needed.

    Args:
        sql: The SQL string to write.
        output_path: Destination file path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql, encoding="utf-8")
    logger.info("DDL written to %s", path)
