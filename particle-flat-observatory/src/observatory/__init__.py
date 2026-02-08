"""Particle Health flat data observatory — schema generation, normalization, and analytics."""

__version__ = "0.1.0"

from observatory.config import ObservatorySettings, load_settings
from observatory.ddl import DDLDialect, generate_ddl, write_ddl
from observatory.normalizer import normalize_record, normalize_resource
from observatory.parser import load_flat_data
from observatory.schema import ResourceSchema, inspect_schema

__all__ = [
    "DDLDialect",
    "ObservatorySettings",
    "ResourceSchema",
    "generate_ddl",
    "inspect_schema",
    "load_flat_data",
    "load_settings",
    "normalize_record",
    "normalize_resource",
    "write_ddl",
]
