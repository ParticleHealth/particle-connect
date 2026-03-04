"""JSON parser for Particle flat data files.

Loads flat_data.json, validates structure, applies normalization,
and returns a dict of resource_type -> list[dict] for all 21 resource types.
"""

import json
import logging
from pathlib import Path

from observatory.normalizer import normalize_resource

logger = logging.getLogger(__name__)

# All 21 resource type keys in the order they appear in the Particle API response.
EXPECTED_RESOURCE_TYPES: list[str] = [
    "aICitations",
    "aIOutputs",
    "allergies",
    "coverages",
    "documentReferences",
    "encounters",
    "familyMemberHistories",
    "immunizations",
    "labs",
    "locations",
    "medications",
    "organizations",
    "patients",
    "practitioners",
    "problems",
    "procedures",
    "recordSources",
    "socialHistories",
    "sources",
    "transitions",
    "vitalSigns",
]


def load_flat_data(path: str | Path, normalize: bool = True) -> dict[str, list[dict]]:
    """Load Particle flat data JSON and return a dict of resource_type -> records.

    Always returns exactly 21 keys (one per expected resource type). Resource types
    missing from the file are included with empty lists. Unknown resource types in
    the file are logged as warnings and skipped.

    Args:
        path: Path to the flat_data.json file.
        normalize: If True (default), convert empty strings to None in all records.

    Returns:
        Dict mapping each of the 21 resource type keys to a list of record dicts.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the top-level JSON structure is not a dict.
    """
    filepath = Path(path)

    if not filepath.exists():
        raise FileNotFoundError(
            f"Flat data file not found: {filepath}. "
            f"Check FLAT_DATA_PATH or provide the correct path to flat_data.json."
        )

    raw = filepath.read_text(encoding="utf-8")
    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected top-level JSON object (dict), got {type(data).__name__}. "
            f"Particle flat data should be a JSON object with resource type keys."
        )

    expected_set = set(EXPECTED_RESOURCE_TYPES)
    result: dict[str, list[dict]] = {}

    # Include expected resource types found in data
    for key in EXPECTED_RESOURCE_TYPES:
        if key in data:
            records = data[key]
            if normalize:
                records = normalize_resource(records)
            result[key] = records
        else:
            logger.info("Resource type %s not found in data, treating as empty", key)
            result[key] = []

    # Warn about unexpected resource types
    for key in data:
        if key not in expected_set:
            logger.warning("Unknown resource type: %s, skipping", key)

    # Log summary
    types_with_counts = ", ".join(f"{k}={len(v)}" for k, v in result.items())
    logger.info("Loaded %d resource types: %s", len(result), types_with_counts)

    return result
