"""Particle Health API Python client library."""

import logging

# Set up NullHandler to avoid "No handler found" warnings
# Applications should configure their own logging handlers
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"

# Query
from particle.query import (
    QueryService,
    QueryRequest,
    QueryResponse,
    PurposeOfUse,
    QueryStatus,
)

# Document
from particle.document import (
    DocumentService,
    DocumentSubmission,
    DocumentResponse,
    DocumentType,
    MimeType,
)

__all__ = [
    # Query
    "QueryService",
    "QueryRequest",
    "QueryResponse",
    "PurposeOfUse",
    "QueryStatus",
    # Document
    "DocumentService",
    "DocumentSubmission",
    "DocumentResponse",
    "DocumentType",
    "MimeType",
]
