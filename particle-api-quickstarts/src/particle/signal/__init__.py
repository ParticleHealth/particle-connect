"""Signal module for Particle Health API.

This module provides:
- Pydantic models for Signal subscriptions, workflows, and webhooks
- Enums for subscription types, workflow types, and ADT event types
- SignalService for subscription, workflow, and data retrieval operations

Usage:
    from particle.core import ParticleSettings, ParticleHTTPClient
    from particle.signal import SignalService, WorkflowType

    settings = ParticleSettings()
    with ParticleHTTPClient(settings) as client:
        service = SignalService(client)

        # Subscribe patient to monitoring
        response = service.subscribe(particle_patient_id="uuid-from-registration")

        # Trigger sandbox workflow
        service.trigger_sandbox_workflow(
            particle_patient_id="uuid-from-registration",
            workflow=WorkflowType.ADMIT_TRANSITION_ALERT,
            callback_url="https://example.com/webhook",
        )
"""

from .models import (
    ADTEventType,
    ReferralOrganization,
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
from .service import SignalService

__all__ = [
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
