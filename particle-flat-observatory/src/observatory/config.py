"""Configuration management for the Particle flat data observatory.

Reads settings from environment variables with sensible defaults.
Optionally loads .env files if python-dotenv is available.
"""

import logging
import os
from dataclasses import dataclass

VALID_DIALECTS = ("postgres", "bigquery")
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

logger = logging.getLogger(__name__)


@dataclass
class ObservatorySettings:
    """Observatory configuration, populated from environment variables."""

    flat_data_path: str
    ddl_dialect: str
    output_dir: str
    log_level: str


def load_settings() -> ObservatorySettings:
    """Load observatory settings from environment variables.

    Attempts to load a .env file via python-dotenv if available (optional).
    Validates DDL_DIALECT and LOG_LEVEL against allowed values.

    Returns:
        ObservatorySettings with resolved configuration.

    Raises:
        ValueError: If DDL_DIALECT is not 'postgres' or 'bigquery'.
        ValueError: If LOG_LEVEL is not a valid Python logging level.
    """
    # Optionally load .env file if python-dotenv is installed
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.debug("Loaded .env file via python-dotenv")
    except ImportError:
        pass

    flat_data_path = os.environ.get("FLAT_DATA_PATH", "sample-data/flat_data.json")
    ddl_dialect = os.environ.get("DDL_DIALECT", "postgres")
    output_dir = os.environ.get("OUTPUT_DIR", "ddl")
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Validate dialect
    if ddl_dialect not in VALID_DIALECTS:
        raise ValueError(
            f"Invalid DDL_DIALECT: '{ddl_dialect}'. "
            f"Must be one of: {', '.join(VALID_DIALECTS)}. "
            f"Set DDL_DIALECT environment variable to 'postgres' or 'bigquery'."
        )

    # Validate log level
    if log_level not in VALID_LOG_LEVELS:
        raise ValueError(
            f"Invalid LOG_LEVEL: '{log_level}'. "
            f"Must be one of: {', '.join(VALID_LOG_LEVELS)}."
        )

    return ObservatorySettings(
        flat_data_path=flat_data_path,
        ddl_dialect=ddl_dialect,
        output_dir=output_dir,
        log_level=log_level,
    )
