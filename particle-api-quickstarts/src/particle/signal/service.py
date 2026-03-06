"""Signal service for Particle Health API operations.

This module provides SignalService which wraps the HTTP client
for Signal-related operations: subscriptions, sandbox workflows,
referral organizations, HL7v2 messages, and transition data.

Usage:
    from particle.core import ParticleSettings, ParticleHTTPClient
    from particle.signal import SignalService, WorkflowType

    settings = ParticleSettings()
    with ParticleHTTPClient(settings) as client:
        service = SignalService(client)

        # Subscribe patient to monitoring
        response = service.subscribe(particle_patient_id)

        # Trigger sandbox workflow
        service.trigger_sandbox_workflow(
            particle_patient_id,
            workflow=WorkflowType.ADMIT_TRANSITION_ALERT,
            callback_url="https://example.com/webhook",
        )
"""

from __future__ import annotations

from particle.core import ParticleHTTPClient
from particle.core.exceptions import ParticleAPIError, ParticleNotFoundError

from .models import (
    ADTEventType,
    ReferralOrganization,
    SubscribeResponse,
    Subscription,
    SubscriptionType,
    TriggerSandboxWorkflowRequest,
    WebhookNotification,
    WorkflowType,
)


class SignalService:
    """Signal subscription, workflow, and data retrieval via Particle Health API."""

    def __init__(self, client: ParticleHTTPClient) -> None:
        """Initialize with an HTTP client.

        Args:
            client: Configured ParticleHTTPClient instance
        """
        self._client = client

    def subscribe(
        self,
        particle_patient_id: str,
        subscription_type: SubscriptionType = SubscriptionType.MONITORING,
    ) -> SubscribeResponse:
        """Subscribe a patient to monitoring.

        Args:
            particle_patient_id: Particle's UUID from patient registration
            subscription_type: Type of subscription (default: MONITORING)

        Returns:
            SubscribeResponse with subscription IDs

        Raises:
            ParticleValidationError: If Particle API rejects the request
            ParticleAPIError: For other API errors
        """
        subscription = Subscription(type=subscription_type)
        payload = {"subscriptions": [subscription.model_dump(mode="json")]}
        try:
            response = self._client.request(
                "POST",
                f"/api/v1/patients/{particle_patient_id}/subscriptions",
                json=payload,
            )
        except ParticleAPIError as e:
            # API returns 400 if subscription already exists — treat as success
            if e.status_code == 400 and e.response_body:
                subs = e.response_body.get("subscriptions", [])
                if any("already exists" in s.get("error", "") for s in subs):
                    return SubscribeResponse(subscriptions=[])
            raise
        return SubscribeResponse.model_validate(response)

    def trigger_sandbox_workflow(
        self,
        particle_patient_id: str,
        workflow: WorkflowType,
        callback_url: str,
        display_name: str = "Test",
        event_type: ADTEventType | None = None,
    ) -> dict:
        """Trigger a sandbox Signal workflow for testing.

        In sandbox mode, this simulates transition alerts without real data.
        For ADT workflows, event_type is required.

        Args:
            particle_patient_id: Particle's UUID from patient registration
            workflow: Type of workflow to trigger
            callback_url: URL where Particle sends webhook notifications
            display_name: Human-readable name for this test
            event_type: Required for ADT workflow; ADT event type (A01-A08)

        Returns:
            Raw API response dict

        Raises:
            ParticleValidationError: If Particle API rejects the request
            ParticleAPIError: For other API errors
        """
        request = TriggerSandboxWorkflowRequest(
            workflow=workflow,
            callback_url=callback_url,
            display_name=display_name,
            event_type=event_type,
        )
        payload = request.model_dump(mode="json", exclude_none=True)
        response = self._client.request(
            "POST",
            f"/api/v1/patients/{particle_patient_id}/subscriptions/trigger-sandbox-workflow",
            json=payload,
        )
        # Sandbox API may return raw text "success" instead of JSON
        if "_raw_content" in response:
            return {"status": response["_raw_content"].decode() if isinstance(response["_raw_content"], bytes) else str(response["_raw_content"])}
        return response

    def register_referral_organizations(
        self,
        organizations: list[ReferralOrganization],
    ) -> dict:
        """Register referral organizations for monitoring.

        Args:
            organizations: List of organizations with OIDs to register

        Returns:
            Raw API response dict

        Raises:
            ParticleValidationError: If Particle API rejects the request
            ParticleAPIError: For other API errors
        """
        payload = {
            "organizations": [
                org.model_dump(mode="json") for org in organizations
            ]
        }
        return self._client.request(
            "POST",
            "/api/v1/referrals/organizations/registered",
            json=payload,
        )

    def get_hl7v2_message(self, message_id: str) -> dict:
        """Retrieve an HL7v2 message by ID.

        Args:
            message_id: UUID of the HL7v2 message

        Returns:
            HL7v2 message data as dict
        """
        return self._client.request(
            "GET",
            f"/hl7v2/{message_id}",
        )

    def get_flat_transitions(self, particle_patient_id: str) -> dict:
        """Retrieve flat data with transitions for a patient.

        Returns transition alert data in Particle's flat JSON format.
        Returns an empty dict if no data is available yet (query not completed).

        Args:
            particle_patient_id: Particle's UUID from patient registration

        Returns:
            Flat transition data as dict, or empty dict if not yet available
        """
        try:
            return self._client.request(
                "GET",
                f"/api/v2/patients/{particle_patient_id}/flat?TRANSITIONS",
            )
        except ParticleNotFoundError:
            return {}

    @staticmethod
    def parse_webhook_notification(payload: dict) -> WebhookNotification:
        """Parse a CloudEvents webhook notification payload.

        Use this to validate and parse incoming webhook requests
        from Particle Signal.

        Args:
            payload: Raw JSON dict from the webhook request body

        Returns:
            Validated WebhookNotification model
        """
        return WebhookNotification.model_validate(payload)
