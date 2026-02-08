"""Particle Health flat data observatory — schema generation, normalization, and analytics."""

__version__ = "0.1.0"

from observatory.config import ObservatorySettings, load_settings
from observatory.normalizer import normalize_record, normalize_resource
from observatory.parser import load_flat_data

__all__ = [
    "ObservatorySettings",
    "load_flat_data",
    "load_settings",
    "normalize_record",
    "normalize_resource",
]
