"""Data quality analysis for Particle flat data.

Analyzes loaded data (Python dicts, not database queries) and produces a
formatted Rich table showing record counts, null percentages, date ranges,
and empty columns per resource type.
"""

import re

from rich.console import Console
from rich.table import Table

from observatory.schema import ResourceSchema

# Simple pattern: value starts with 4 digits (YYYY) indicating a date/timestamp
_DATE_PATTERN = re.compile(r"^\d{4}-")


def analyze_quality(
    data: dict[str, list[dict]], schemas: list[ResourceSchema]
) -> list[dict]:
    """Analyze data quality for each non-empty resource type.

    Operates on the in-memory data dict (not the database), so it works
    regardless of whether the database load succeeded.

    Args:
        data: Dict from load_flat_data -- resource_type -> list of record dicts.
        schemas: List of ResourceSchema objects from inspect_schema.

    Returns:
        List of quality result dicts sorted by record_count descending.
        Each dict has keys: table_name, record_count, column_count, null_pct,
        date_range, empty_columns.
    """
    results: list[dict] = []

    for schema in schemas:
        if schema.is_empty:
            continue

        records = data.get(schema.resource_type, [])
        if not records:
            continue

        columns = schema.columns
        record_count = len(records)
        column_count = len(columns)
        total_fields = record_count * column_count

        # Count nulls and track per-column all-null status
        total_nulls = 0
        column_null_counts: dict[str, int] = {col: 0 for col in columns}
        date_values: list[str] = []

        for record in records:
            for col in columns:
                value = record.get(col)
                if value is None:
                    total_nulls += 1
                    column_null_counts[col] += 1
                else:
                    # Check if this value looks like a date/timestamp
                    if isinstance(value, str) and _DATE_PATTERN.match(value):
                        date_values.append(value[:10])

        # Null percentage
        null_pct = (total_nulls / total_fields * 100) if total_fields > 0 else 0.0

        # Date range
        if date_values:
            min_date = min(date_values)
            max_date = max(date_values)
            date_range = f"{min_date} to {max_date}"
        else:
            date_range = "n/a"

        # Empty columns (all values None)
        empty_cols = sum(1 for col in columns if column_null_counts[col] == record_count)

        results.append({
            "table_name": schema.table_name,
            "record_count": record_count,
            "column_count": column_count,
            "null_pct": null_pct,
            "date_range": date_range,
            "empty_columns": empty_cols,
        })

    # Sort by record_count descending (largest tables first)
    results.sort(key=lambda r: r["record_count"], reverse=True)

    return results


def print_quality_report(results: list[dict]) -> None:
    """Print a formatted Rich table summarizing data quality.

    Args:
        results: List of quality result dicts from analyze_quality.
    """
    console = Console()

    table = Table(title="Data Quality Report")
    table.add_column("Table", style="cyan")
    table.add_column("Records", justify="right", style="green")
    table.add_column("Columns", justify="right")
    table.add_column("Null %", justify="right")
    table.add_column("Date Range", style="dim")
    table.add_column("Empty Cols", justify="right")

    total_records = 0
    total_null_pct = 0.0
    total_empty_cols = 0

    for r in results:
        # Color-code null percentage
        null_pct = r["null_pct"]
        if null_pct > 80:
            null_style = "red"
        elif null_pct > 50:
            null_style = "yellow"
        else:
            null_style = ""

        # Color-code empty columns
        empty_style = "red" if r["empty_columns"] > 0 else ""

        table.add_row(
            r["table_name"],
            str(r["record_count"]),
            str(r["column_count"]),
            f"[{null_style}]{null_pct:.1f}%[/{null_style}]" if null_style else f"{null_pct:.1f}%",
            r["date_range"],
            f"[{empty_style}]{r['empty_columns']}[/{empty_style}]"
            if empty_style
            else str(r["empty_columns"]),
        )

        total_records += r["record_count"]
        total_null_pct += null_pct
        total_empty_cols += r["empty_columns"]

    # Footer row with totals
    avg_null = total_null_pct / len(results) if results else 0.0
    table.add_section()
    table.add_row(
        "TOTAL",
        str(total_records),
        "",
        f"{avg_null:.1f}%",
        "",
        str(total_empty_cols),
        style="bold",
    )

    console.print(table)

    table_count = len(results)
    console.print(f"\nLoaded {total_records} records across {table_count} tables")
