"""Pydantic models and enums for the ToC workflow."""

from enum import Enum
from pydantic import BaseModel


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    DATA_GATHERING = "data_gathering"
    GATE_1_PENDING = "gate_1_pending"
    CALLING = "calling"
    GATE_2_PENDING = "gate_2_pending"
    EMAILING = "emailing"
    GATE_3_PENDING = "gate_3_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GateDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


# --- Request models ---

class CreateWorkflowRequest(BaseModel):
    patient_id: str = "care-coord-toc-demo"
    given_name: str = "Elvira"
    family_name: str = "Valadez-Nucleus"
    date_of_birth: str = "1970-12-26"
    gender: str = "FEMALE"
    postal_code: str = "02215"
    address_city: str = "Boston"
    address_state: str = "MA"
    telephone: str = "234-567-8910"
    email: str = ""


class GateDecisionRequest(BaseModel):
    decision: GateDecision
    coordinator_notes: str = ""
    decided_by: str = "coordinator"


# --- Response models ---

class WorkflowSummary(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    status: WorkflowStatus
    current_step: str
    created_at: str
    updated_at: str


class GateStatus(BaseModel):
    gate_number: int
    status: str  # pending | approved | rejected | escalated
    decision: GateDecision | None = None
    coordinator_notes: str | None = None
    decided_by: str | None = None
    decided_at: str | None = None


class WorkflowEvent(BaseModel):
    id: int
    workflow_id: str
    event_type: str
    event_data: dict | None = None
    created_at: str


class PatientContextResponse(BaseModel):
    workflow_id: str
    context: dict
    care_gaps: list[dict]
    created_at: str


class CallResultResponse(BaseModel):
    workflow_id: str
    call_id: str | None = None
    status: str
    duration_ms: int | None = None
    transcript: str | None = None
    disposition_action: str | None = None
    disposition_params: dict | None = None
    created_at: str


class EmailRecordResponse(BaseModel):
    workflow_id: str
    recipient_email: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    status: str
    created_at: str


class WorkflowDetail(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    status: WorkflowStatus
    current_step: str
    created_at: str
    updated_at: str
    error_message: str | None = None
    patient_context: PatientContextResponse | None = None
    call_result: CallResultResponse | None = None
    email_record: EmailRecordResponse | None = None
    gate_decisions: list[GateStatus] = []
    events: list[WorkflowEvent] = []
