"""Typer CLI entry point for the Particle flat data pipeline.

Wires together the parser (or API client), schema inspector, and database
loader into a single `particle-pipeline` command with .env loading,
actionable error messages, and --help usage.
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
VALID_TARGETS = ("duckdb", "bigquery")


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
        str, typer.Option("--target", help="Target database: 'duckdb' or 'bigquery'")
    ] = "duckdb",
    data_path: Annotated[
        str,
        typer.Option(
            "--data-path",
            help="Path to flat_data.json",
            envvar="FLAT_DATA_PATH",
        ),
    ] = "sample-data/flat_data.json",
    patient_id: Annotated[
        str | None,
        typer.Option(
            "--patient-id",
            help="Patient ID for API source",
            envvar="PARTICLE_PATIENT_ID",
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable debug logging")
    ] = False,
) -> None:
    """Load Particle flat data into a target database.

    Parses a flat_data.json file (or fetches from the Particle API), inspects
    the schema, and loads all resource types into the target database with
    idempotent semantics (safe to re-run).

    Examples:

        particle-pipeline

        particle-pipeline --target bigquery

        particle-pipeline --data-path /path/to/flat_data.json

        particle-pipeline --source api --patient-id abc-123 --target duckdb

        particle-pipeline --verbose
    """
    _configure_logging(verbose)

    # Validate source
    if source not in VALID_SOURCES:
        typer.echo(
            f"Invalid source: '{source}'. Must be one of: {', '.join(VALID_SOURCES)}"
        )
        raise typer.Exit(code=1)

    # Validate target
    if target not in VALID_TARGETS:
        typer.echo(
            f"Invalid target: '{target}'. Must be one of: {', '.join(VALID_TARGETS)}"
        )
        raise typer.Exit(code=1)
    typer.echo(f"Loading Particle flat data (source={source}, target={target})")

    # --- Fetch or parse flat data ---
    if source == "api":
        if not patient_id:
            typer.echo(
                "--patient-id is required when --source api\n\n"
                "Usage: particle-pipeline --source api "
                "--patient-id <patient-id> --target postgres"
            )
            raise typer.Exit(code=1)

        from observatory.api_client import ParticleAPIClient

        try:
            api_client = ParticleAPIClient()
        except ValueError as e:
            typer.echo(str(e))
            raise typer.Exit(code=1)

        try:
            raw_data = api_client.get_flat_data(patient_id)
        except Exception as e:
            typer.echo(f"API request failed: {e}")
            raise typer.Exit(code=1)

        # Apply same normalization as file mode for identical downstream behavior
        from observatory.normalizer import normalize_resource
        from observatory.parser import EXPECTED_RESOURCE_TYPES

        data: dict[str, list[dict]] = {}
        for key in EXPECTED_RESOURCE_TYPES:
            records = raw_data.get(key, [])
            data[key] = normalize_resource(records)

    else:
        # --- File source (default) ---
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

    elif target == "duckdb":
        from observatory.loader import get_connection, load_all

        db_path = os.environ.get("DUCKDB_PATH", "observatory.duckdb")

        try:
            conn = get_connection(db_path)
            results = load_all(conn, data, schemas)
            conn.close()
        except Exception as e:
            typer.echo(
                f"Could not open DuckDB at {db_path}: {e}\n\n"
                "To fix: check DUCKDB_PATH in .env or ensure the directory is writable"
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
