"""BigQuery loader for Particle flat data.

Implements idempotent delete+insert per patient_id per resource type,
using google-cloud-bigquery batch load jobs (load_table_from_json).
"""

import logging
import os

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None  # type: ignore[assignment]

from observatory.schema import ResourceSchema

logger = logging.getLogger(__name__)


def get_bq_client() -> tuple:
    """Create a BigQuery client from environment variables.

    Reads BQ_PROJECT_ID (required) and BQ_DATASET (optional, defaults to
    "particle_observatory") from the environment.

    Returns:
        Tuple of (bigquery.Client, dataset_id).

    Raises:
        ImportError: If google-cloud-bigquery is not installed.
        ValueError: If BQ_PROJECT_ID is not set.
    """
    if bigquery is None:
        raise ImportError(
            "google-cloud-bigquery is not installed. "
            "Install with: pip install -e '.[bigquery]'"
        )

    project_id = os.environ.get("BQ_PROJECT_ID", "")
    if not project_id:
        raise ValueError(
            "BQ_PROJECT_ID not set. "
            "Set BQ_PROJECT_ID in .env or environment to your GCP project ID."
        )

    dataset_id = os.environ.get("BQ_DATASET", "particle_observatory")

    client = bigquery.Client(project=project_id)
    logger.info("BigQuery client created for project=%s, dataset=%s", project_id, dataset_id)
    return (client, dataset_id)


def load_resource_bq(client, dataset_id: str, table_name: str,
                     columns: list[str], records: list[dict],
                     patient_id: str) -> int:
    """Load records for a single resource type and patient into BigQuery.

    Uses idempotent delete+insert: first deletes all existing rows for the
    patient_id using a parameterized DELETE query, then inserts the new
    records via a batch load job (load_table_from_json).

    Args:
        client: A BigQuery client instance.
        dataset_id: The BigQuery dataset ID.
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

    # Backtick-quoted table reference for SQL queries
    table_ref_sql = f"`{client.project}.{dataset_id}.{table_name}`"
    # Dotted table reference for API calls (load_table_from_json)
    table_ref_api = f"{client.project}.{dataset_id}.{table_name}"

    # Step 1: DELETE existing rows for this patient
    delete_query = f"DELETE FROM {table_ref_sql} WHERE `patient_id` = @patient_id"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("patient_id", "STRING", patient_id),
        ]
    )
    client.query(delete_query, job_config=job_config).result()

    # Step 2: INSERT new records via batch load job
    schema = [bigquery.SchemaField(col, "STRING", mode="NULLABLE") for col in columns]
    rows = [{col: record.get(col) for col in columns} for record in records]
    load_config = bigquery.LoadJobConfig(schema=schema)
    client.load_table_from_json(rows, table_ref_api, job_config=load_config).result()

    count = len(records)
    logger.info(
        "Loaded %d records into %s for patient %s",
        count, table_name, patient_id,
    )
    return count


def load_all_bq(client, dataset_id: str, data: dict[str, list[dict]],
                schemas: list[ResourceSchema]) -> dict[str, int]:
    """Load all resource types into BigQuery.

    Iterates over schemas (not data keys) for consistent ordering. Skips
    empty schemas (no table exists) and resource types with no records.
    Loads per-patient for idempotency: each patient_id gets its own
    delete+insert cycle per resource type.

    Args:
        client: A BigQuery client instance.
        dataset_id: The BigQuery dataset ID.
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
            count = load_resource_bq(
                client=client,
                dataset_id=dataset_id,
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
