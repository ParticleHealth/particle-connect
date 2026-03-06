"""Particle Health API Python client library."""

import logging

# Document
from particle.document import (
    DocumentResponse,
    DocumentService,
    DocumentSubmission,
    DocumentType,
    MimeType,
)

# Patient
from particle.patient import (
    Gender,
    PatientRegistration,
    PatientResponse,
    PatientService,
)

# Query
from particle.query import (
    PurposeOfUse,
    QueryRequest,
    QueryResponse,
    QueryService,
    QueryStatus,
)

# Signal
from particle.signal import (
    ADTEventType,
    ReferralOrganization,
    SignalService,
    SubscribeResponse,
    Subscription,
    SubscriptionResponse,
    SubscriptionType,
    TransitionResource,
    TriggerSandboxWorkflowRequest,
    WebhookNotification,
    WebhookNotificationData,
    WorkflowType,
)

# Set up NullHandler to avoid "No handler found" warnings
# Applications should configure their own logging handlers
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"

__all__ = [
    # Patient
    "PatientService",
    "PatientRegistration",
    "PatientResponse",
    "Gender",
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
    # Signal
    "SignalService",
    "SubscriptionType",
    "WorkflowType",
    "ADTEventType",
    "Subscription",
    "SubscriptionResponse",
    "SubscribeResponse",
    "TriggerSandboxWorkflowRequest",
    "ReferralOrganization",
    "TransitionResource",
    "WebhookNotificationData",
    "WebhookNotification",
]
