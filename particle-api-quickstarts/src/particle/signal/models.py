"""Pydantic models for Signal (monitoring & transition alerts) with Particle Health API.

This module provides validated data models for Signal operations:
- SubscriptionType: Enum for subscription types (MONITORING)
- WorkflowType: Enum for sandbox workflow triggers
- ADTEventType: Enum for ADT event types (A01-A08)
- Subscription/SubscriptionResponse: Models for patient monitoring subscriptions
- TriggerSandboxWorkflowRequest: Input model for sandbox workflow triggers
- ReferralOrganization: Model for referral organization registration
- WebhookNotification: CloudEvents-formatted webhook notification model
- TransitionResource: Resource reference in webhook notification data

Signal Flow:
1. Subscribe patient to monitoring (POST /api/v1/patients/{id}/subscriptions)
2. Register referral organizations (POST /api/v1/referrals/organizations/registered)
3. Receive webhook notifications when transitions occur
4. Retrieve HL7v2 messages or flat data with transitions
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionType(str, Enum):
    """Subscription types for patient monitoring.

    - MONITORING: Subscribe patient for transition alert monitoring
    """

    MONITORING = "MONITORING"


class WorkflowType(str, Enum):
    """Valid sandbox workflow types for trigger-sandbox-workflow endpoint.

    - ADMIT_TRANSITION_ALERT: Simulates hospital admission alert
    - DISCHARGE_TRANSITION_ALERT: Simulates hospital discharge alert
    - TRANSFER_TRANSITION_ALERT: Simulates hospital transfer alert
    - NEW_ENCOUNTER_ALERT: Simulates new encounter alert
    - REFERRAL_ALERT: Simulates referral alert
    - ADT: Simulates raw ADT message (requires event_type)
    - DISCHARGE_SUMMARY_ALERT: Simulates discharge summary alert
    """

    ADMIT_TRANSITION_ALERT = "ADMIT_TRANSITION_ALERT"
    DISCHARGE_TRANSITION_ALERT = "DISCHARGE_TRANSITION_ALERT"
    TRANSFER_TRANSITION_ALERT = "TRANSFER_TRANSITION_ALERT"
    NEW_ENCOUNTER_ALERT = "NEW_ENCOUNTER_ALERT"
    REFERRAL_ALERT = "REFERRAL_ALERT"
    ADT = "ADT"
    DISCHARGE_SUMMARY_ALERT = "DISCHARGE_SUMMARY_ALERT"


class ADTEventType(str, Enum):
    """Valid ADT event types for ADT workflow triggers.

    - A01: Admit/Visit Notification
    - A02: Transfer a Patient
    - A03: Discharge/End Visit
    - A04: Register a Patient
    - A08: Update Patient Information
    """

    A01 = "A01"
    A02 = "A02"
    A03 = "A03"
    A04 = "A04"
    A08 = "A08"


class Subscription(BaseModel):
    """A single subscription entry for request payloads.

    Attributes:
        type: Subscription type (e.g., MONITORING)
    """

    type: SubscriptionType = SubscriptionType.MONITORING


class SubscriptionResponse(BaseModel):
    """A single subscription entry returned by the API.

    Attributes:
        id: Particle-assigned subscription UUID
        type: Subscription type
    """

    id: str
    type: SubscriptionType

    model_config = ConfigDict(extra="ignore")


class SubscribeResponse(BaseModel):
    """Response from subscribing a patient to monitoring.

    The sandbox API may return an empty body on success.

    Attributes:
        subscriptions: List of created subscriptions with IDs (empty if not returned)
    """

    subscriptions: list[SubscriptionResponse] = []

    model_config = ConfigDict(extra="ignore")


class TriggerSandboxWorkflowRequest(BaseModel):
    """Request model for triggering a sandbox Signal workflow.

    Attributes:
        workflow: The type of workflow to trigger
        callback_url: URL where Particle will send webhook notifications
        display_name: Human-readable name for the test workflow
        event_type: Required for ADT workflow; specifies the ADT event type
    """

    workflow: WorkflowType
    callback_url: str
    display_name: str = "Test"
    event_type: ADTEventType | None = None


class ReferralOrganization(BaseModel):
    """A referral organization identified by OID.

    Attributes:
        oid: Organization Identifier (OID) string
    """

    oid: str = Field(..., min_length=1)


class TransitionResource(BaseModel):
    """Resource reference in a webhook notification.

    Attributes:
        file_id: UUID of the file containing the resource
        resource_ids: List of resource identifier paths
    """

    file_id: str
    resource_ids: list[str] = []

    model_config = ConfigDict(extra="ignore")


class WebhookNotificationData(BaseModel):
    """Data payload within a CloudEvents webhook notification.

    Attributes:
        particle_patient_id: Particle's UUID for the patient
        event_type: Type of transition event (e.g., "Admission")
        event_sequence: Sequence number for ordered event processing
        is_final_event: Whether this is the last event in the sequence
        resources: List of associated file/resource references
    """

    particle_patient_id: str
    event_type: str | None = None
    event_sequence: int | None = None
    is_final_event: bool | None = None
    resources: list[TransitionResource] = []

    model_config = ConfigDict(extra="ignore")


class WebhookNotification(BaseModel):
    """CloudEvents-formatted webhook notification from Particle Signal.

    Particle sends these to your callback_url when transition alerts fire.

    Attributes:
        specversion: CloudEvents spec version (always "1.0")
        type: Event type identifier (e.g., "com.particlehealth.api.v2.transitionalerts")
        subject: Human-readable event subject (e.g., "Hospital Admit")
        source: Event source path
        id: Unique notification UUID
        time: Timestamp of the notification
        datacontenttype: Content type of the data field
        data: Notification payload with patient and resource details
    """

    specversion: str = "1.0"
    type: str
    subject: str | None = None
    source: str | None = None
    id: str
    time: datetime | None = None
    datacontenttype: str | None = None
    data: WebhookNotificationData

    model_config = ConfigDict(extra="ignore")
