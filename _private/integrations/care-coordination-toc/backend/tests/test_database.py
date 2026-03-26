"""Tests for database CRUD operations."""

import pytest


def test_create_and_get_workflow(db, sample_demographics):
    wf = db.create_workflow("patient-1", "Test Patient", sample_demographics)
    assert wf["id"]
    assert wf["patient_id"] == "patient-1"
    assert wf["patient_name"] == "Test Patient"
    assert wf["status"] == "pending"

    fetched = db.get_workflow(wf["id"])
    assert fetched["id"] == wf["id"]


def test_list_workflows(db, sample_demographics):
    db.create_workflow("p1", "Patient 1", sample_demographics)
    db.create_workflow("p2", "Patient 2", sample_demographics)
    all_wf = db.list_workflows()
    assert len(all_wf) == 2

    db.update_workflow_status(all_wf[0]["id"], "completed", "done")
    completed = db.list_workflows(status="completed")
    assert len(completed) == 1


def test_update_workflow_status(db, sample_demographics):
    wf = db.create_workflow("p1", "Test", sample_demographics)
    db.update_workflow_status(wf["id"], "data_gathering", "data")
    updated = db.get_workflow(wf["id"])
    assert updated["status"] == "data_gathering"
    assert updated["current_step"] == "data"


def test_patient_context(db, sample_demographics):
    wf = db.create_workflow("p1", "Test", sample_demographics)
    ctx = {"patient_first_name": "Test", "facility_name": "Boston General"}
    gaps = [{"type": "high_risk", "severity": "high", "detail": "CHF"}]
    db.store_patient_context(wf["id"], ctx, gaps)

    result = db.get_patient_context(wf["id"])
    assert result["context"]["patient_first_name"] == "Test"
    assert len(result["care_gaps"]) == 1


def test_call_result(db, sample_demographics):
    wf = db.create_workflow("p1", "Test", sample_demographics)
    db.store_call_result(
        wf["id"], "call-123", "completed", 180000,
        "Hi, this is Sarah...", "schedule_followup_call",
        {"days_from_now": 7, "notes": "Patient doing well"},
    )
    result = db.get_call_result(wf["id"])
    assert result["call_id"] == "call-123"
    assert result["disposition_action"] == "schedule_followup_call"
    assert result["disposition_params"]["days_from_now"] == 7


def test_email_record(db, sample_demographics):
    wf = db.create_workflow("p1", "Test", sample_demographics)
    db.store_email_record(
        wf["id"], "test@example.com", "Follow-up",
        "<html>body</html>", "plain body", "draft",
    )
    result = db.get_email_record(wf["id"])
    assert result["status"] == "draft"

    db.update_email_status(wf["id"], "sent")
    result = db.get_email_record(wf["id"])
    assert result["status"] == "sent"


def test_gate_decisions(db, sample_demographics):
    wf = db.create_workflow("p1", "Test", sample_demographics)
    db.store_gate_decision(wf["id"], 1, "approved", "Looks good", "coordinator")
    decision = db.get_gate_decision(wf["id"], 1)
    assert decision["decision"] == "approved"
    assert decision["coordinator_notes"] == "Looks good"

    # No decision for gate 2 yet
    assert db.get_gate_decision(wf["id"], 2) is None


def test_workflow_events(db, sample_demographics):
    wf = db.create_workflow("p1", "Test", sample_demographics)
    db.log_event(wf["id"], "step_started", {"step": "data_gathering"})
    db.log_event(wf["id"], "step_completed", {"step": "data_gathering"})

    events = db.list_events(wf["id"])
    assert len(events) == 2
    assert events[0]["event_type"] == "step_started"
    assert events[0]["event_data"]["step"] == "data_gathering"


def test_get_nonexistent_workflow(db):
    assert db.get_workflow("does-not-exist") is None
