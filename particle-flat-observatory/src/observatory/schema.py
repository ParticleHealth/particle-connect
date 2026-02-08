"""Schema inspection for Particle flat data.

Discovers column names per resource type by scanning all records,
and converts camelCase resource type keys to snake_case table names.
"""

import logging
import re
from dataclasses import dataclass

from observatory.parser import EXPECTED_RESOURCE_TYPES

logger = logging.getLogger(__name__)


@dataclass
class ResourceSchema:
    """Schema for a single Particle resource type."""

    resource_type: str
    """The camelCase key from the Particle API (e.g., "aICitations")."""

    table_name: str
    """The snake_case SQL table name (e.g., "ai_citations")."""

    columns: list[str]
    """Ordered list of column names discovered from data."""

    record_count: int
    """Number of records found for this resource type."""

    is_empty: bool
    """True if no records were found (0 records)."""


def camel_to_snake(name: str) -> str:
    """Convert a camelCase resource type key to a snake_case table name.

    Handles the Particle-specific "aI" prefix (aICitations -> ai_citations)
    and standard camelCase conversions (vitalSigns -> vital_signs).
    """
    # Special-case: leading "aI" prefix should become "ai_", not "a_i_"
    if name.startswith("aI") and len(name) > 2 and name[2].isupper():
        name = "ai" + name[2:]

    # Insert underscore before uppercase letters that follow lowercase letters
    result = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    # Insert underscore before uppercase letters followed by lowercase (for acronyms)
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", result)
    return result.lower()


def inspect_schema(data: dict[str, list[dict]]) -> list[ResourceSchema]:
    """Discover the schema (column names) for each resource type in the data.

    Scans ALL records for each resource type to build the full set of column names.
    Column order preserves the order columns are first encountered across records
    (not alphabetical). This matches the JSON key order from the Particle API.

    Args:
        data: Dict from load_flat_data — resource_type -> list of record dicts.

    Returns:
        List of ResourceSchema objects, sorted by EXPECTED_RESOURCE_TYPES order.
    """
    # Build order from EXPECTED_RESOURCE_TYPES, then append any extras
    type_order = list(EXPECTED_RESOURCE_TYPES)
    for key in data:
        if key not in type_order:
            type_order.append(key)

    schemas: list[ResourceSchema] = []

    for resource_type in type_order:
        if resource_type not in data:
            continue

        records = data[resource_type]

        # Discover all columns by scanning every record, preserving first-seen order
        seen_columns: dict[str, None] = {}
        for record in records:
            for key in record:
                if key not in seen_columns:
                    seen_columns[key] = None

        columns = list(seen_columns.keys())

        schema = ResourceSchema(
            resource_type=resource_type,
            table_name=camel_to_snake(resource_type),
            columns=columns,
            record_count=len(records),
            is_empty=len(records) == 0,
        )
        schemas.append(schema)

    non_empty = sum(1 for s in schemas if not s.is_empty)
    empty = sum(1 for s in schemas if s.is_empty)
    logger.info(
        "%d resource types inspected, %d non-empty, %d empty",
        len(schemas),
        non_empty,
        empty,
    )

    return schemas
