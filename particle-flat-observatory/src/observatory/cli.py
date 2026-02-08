"""Typer CLI entry point for the Particle flat data pipeline.

Wires together the parser, schema inspector, and PostgreSQL loader into a
single `particle-pipeline load` command with .env loading, actionable error
messages, and --help usage.
"""

import logging
import os
from typing import Annotated

import typer
from dotenv import load_dotenv

# Load .env before typer processes env vars
load_dotenv()

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="particle-pipeline",
    help="Particle Health flat data pipeline -- load, transform, and analyze.",
    no_args_is_help=True,
)

VALID_SOURCES = ("file", "api")
VALID_TARGETS = ("postgres", "bigquery")


def _configure_logging(verbose: bool) -> None:
    """Configure root logger with timestamp, level, and message."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if verbose:
        level = logging.DEBUG
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        level=level,
        force=True,
    )


@app.command()
def load(
    source: Annotated[
        str, typer.Option("--source", help="Data source: 'file' or 'api'")
    ] = "file",
    target: Annotated[
        str, typer.Option("--target", help="Target database: 'postgres' or 'bigquery'")
    ] = "postgres",
    data_path: Annotated[
        str,
        typer.Option(
            "--data-path",
            help="Path to flat_data.json",
            envvar="FLAT_DATA_PATH",
        ),
    ] = "sample-data/flat_data.json",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable debug logging")
    ] = False,
) -> None:
    """Load Particle flat data into a target database.

    Parses a flat_data.json file, inspects the schema, and loads all resource
    types into the target database with idempotent semantics (safe to re-run).

    Examples:

        particle-pipeline load

        particle-pipeline load --target bigquery

        particle-pipeline load --data-path /path/to/flat_data.json

        particle-pipeline load --verbose
    """
    _configure_logging(verbose)

    # Validate source
    if source not in VALID_SOURCES:
        typer.echo(
            f"Invalid source: '{source}'. Must be one of: {', '.join(VALID_SOURCES)}"
        )
        raise typer.Exit(code=1)
    if source == "api":
        typer.echo("API source not yet implemented (coming in Phase 5)")
        raise typer.Exit(code=1)

    # Validate target
    if target not in VALID_TARGETS:
        typer.echo(
            f"Invalid target: '{target}'. Must be one of: {', '.join(VALID_TARGETS)}"
        )
        raise typer.Exit(code=1)
    typer.echo(f"Loading Particle flat data (source={source}, target={target})")

    # --- Parse flat data ---
    from observatory.parser import load_flat_data

    try:
        data = load_flat_data(data_path)
    except FileNotFoundError:
        typer.echo(
            f"Data file not found: {data_path}\n\n"
            "To fix: check --data-path or set FLAT_DATA_PATH in .env"
        )
        raise typer.Exit(code=1)

    # --- Inspect schema ---
    from observatory.schema import inspect_schema

    schemas = inspect_schema(data)

    non_empty = [s for s in schemas if not s.is_empty]
    total_records = sum(s.record_count for s in schemas)
    typer.echo(f"Found {len(non_empty)} resource types with {total_records} total records")

    # --- Load into target database ---
    if target == "bigquery":
        try:
            from observatory.bq_loader import get_bq_client, load_all_bq
        except Exception as e:
            typer.echo(
                f"Could not load BigQuery module: {e}\n\n"
                "To fix:\n"
                "  1. Install BigQuery support: pip install -e '.[bigquery]'\n"
                "  2. Verify installation: python -c \"from google.cloud import bigquery\""
            )
            raise typer.Exit(code=1)

        try:
            client, dataset_id = get_bq_client()
        except ValueError as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(
                f"Could not connect to BigQuery: {e}\n\n"
                "To fix:\n"
                "  1. Install BigQuery support: pip install -e '.[bigquery]'\n"
                "  2. Set BQ_PROJECT_ID in .env to your GCP project ID\n"
                "  3. Authenticate: gcloud auth application-default login"
            )
            raise typer.Exit(code=1)

        results = load_all_bq(client, dataset_id, data, schemas)

    elif target == "postgres":
        import psycopg

        from observatory.loader import get_connection_string, load_all

        conn_string = get_connection_string()

        # Extract host/port for error messages
        pg_host = os.environ.get("PG_HOST", "localhost")
        pg_port = os.environ.get("PG_PORT", "5432")

        try:
            with psycopg.connect(conn_string) as conn:
                results = load_all(conn, data, schemas)
        except psycopg.OperationalError:
            typer.echo(
                f"Could not connect to PostgreSQL at {pg_host}:{pg_port}\n\n"
                "To fix:\n"
                "  1. Start the database: docker compose up -d\n"
                "  2. Wait for healthy: docker compose ps\n"
                f"  3. Check connection: PG_HOST={pg_host} PG_PORT={pg_port} in .env"
            )
            raise typer.Exit(code=1)

    tables_loaded = len(results)
    records_loaded = sum(results.values())
    typer.echo(f"Loaded {records_loaded} records into {tables_loaded} tables")

    # --- Data quality report ---
    from observatory.quality import analyze_quality, print_quality_report

    quality_results = analyze_quality(data, schemas)
    print_quality_report(quality_results)

    typer.echo("Done.")
