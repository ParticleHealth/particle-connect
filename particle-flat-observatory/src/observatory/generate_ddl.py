"""CLI entry point for generating DDL from Particle flat data.

Loads flat_data.json, inspects the schema, and generates CREATE TABLE SQL
for PostgreSQL and/or BigQuery. Output files are written to the specified
output directory as static SQL artifacts that can be reviewed and hand-edited.

Usage:
    python -m observatory.generate_ddl --dialect all
    python -m observatory.generate_ddl --dialect postgres --data-path sample-data/flat_data.json
    observatory-generate-ddl --dialect bigquery --output-dir ddl
"""

import argparse
import logging
import os
import sys

from observatory.ddl import generate_ddl, write_ddl
from observatory.parser import load_flat_data
from observatory.schema import inspect_schema

logger = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments, using environment variables as defaults."""
    parser = argparse.ArgumentParser(
        description="Generate DDL (CREATE TABLE) SQL from Particle flat data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Environment variables (overridden by CLI args):\n"
            "  FLAT_DATA_PATH  Path to flat_data.json (default: sample-data/flat_data.json)\n"
            "  DDL_DIALECT     duckdb, postgres, bigquery, or all (default: duckdb)\n"
            "  OUTPUT_DIR      Output directory for DDL files (default: ddl)\n"
        ),
    )
    parser.add_argument(
        "--data-path",
        default=os.environ.get("FLAT_DATA_PATH", "sample-data/flat_data.json"),
        help="Path to flat_data.json (default: FLAT_DATA_PATH env or sample-data/flat_data.json)",
    )
    parser.add_argument(
        "--dialect",
        default=os.environ.get("DDL_DIALECT", "all"),
        choices=["duckdb", "postgres", "bigquery", "all"],
        help="SQL dialect: duckdb, postgres, bigquery, or all (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR", "ddl"),
        help="Output directory for generated DDL files (default: ddl)",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        default=False,
        help="Skip empty string -> NULL normalization (for debugging)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for DDL generation."""
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Determine which dialects to generate
    if args.dialect == "all":
        dialects = ["duckdb", "postgres", "bigquery"]
    else:
        dialects = [args.dialect]

    # Load and inspect data
    logger.info("Loading flat data from %s", args.data_path)
    data = load_flat_data(args.data_path, normalize=not args.no_normalize)
    schemas = inspect_schema(data)

    non_empty = sum(1 for s in schemas if not s.is_empty)
    empty = sum(1 for s in schemas if s.is_empty)

    # Generate DDL for each dialect
    for dialect in dialects:
        sql = generate_ddl(schemas, dialect)
        output_path = os.path.join(args.output_dir, dialect, "create_all.sql")
        write_ddl(sql, output_path)

        print(f"Generated DDL for {dialect}:")
        print(f"  Tables: {len(schemas)} ({non_empty} with columns, {empty} empty)")
        print(f"  Output: {output_path}")

    logger.info("DDL generation complete")


if __name__ == "__main__":
    sys.exit(main() or 0)
