"""Tests for the orchestrator state machine."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import Orchestrator, TRANSITIONS


def test_all_transitions_defined():
    """Verify all non-terminal states have transitions."""
    terminal = {"completed", "failed", "cancelled"}
    for status in ["pending", "data_gathering", "gate_1_pending", "calling",
                    "gate_2_pending", "emailing", "gate_3_pending"]:
        assert status in TRANSITIONS, f"Missing transitions for {status}"


def test_happy_path(db, sample_demographics):
    """Test full workflow from pending to completed."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    # pending -> data_gathering
    new = orch._transition(wf["id"], "start")
    assert new == "data_gathering"

    # data_gathering -> gate_1_pending
    new = orch._transition(wf["id"], "complete")
    assert new == "gate_1_pending"

    # gate_1_pending -> calling (via approve)
    new = orch._transition(wf["id"], "approve")
    assert new == "calling"

    # calling -> gate_2_pending
    new = orch._transition(wf["id"], "complete")
    assert new == "gate_2_pending"

    # gate_2_pending -> emailing (via approve)
    new = orch._transition(wf["id"], "approve")
    assert new == "emailing"

    # emailing -> gate_3_pending
    new = orch._transition(wf["id"], "complete")
    assert new == "gate_3_pending"

    # gate_3_pending -> completed (via approve)
    new = orch._transition(wf["id"], "approve")
    assert new == "completed"


def test_gate_rejection(db, sample_demographics):
    """Test gate rejection cancels workflow."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    orch._transition(wf["id"], "start")
    orch._transition(wf["id"], "complete")

    # Reject at gate 1 -> cancelled
    new = orch._transition(wf["id"], "reject")
    assert new == "cancelled"


def test_gate_2_rejection_completes(db, sample_demographics):
    """Test gate 2 rejection completes (closes without email)."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    orch._transition(wf["id"], "start")
    orch._transition(wf["id"], "complete")
    orch._transition(wf["id"], "approve")
    orch._transition(wf["id"], "complete")

    # Reject at gate 2 -> completed
    new = orch._transition(wf["id"], "reject")
    assert new == "completed"


def test_failure_handling(db, sample_demographics):
    """Test agent failure transitions to failed."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    orch._transition(wf["id"], "start")
    new = orch._transition(wf["id"], "fail")
    assert new == "failed"


def test_invalid_transition(db, sample_demographics):
    """Test invalid transition raises error."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    with pytest.raises(ValueError, match="Invalid transition"):
        orch._transition(wf["id"], "approve")  # Can't approve from pending


def test_process_gate_decision(db, sample_demographics):
    """Test processing a gate decision."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    orch._transition(wf["id"], "start")
    orch._transition(wf["id"], "complete")

    # Process gate 1 decision
    new = orch.process_gate_decision(wf["id"], 1, "approved", "All clear", "nurse-1")
    assert new == "calling"

    # Verify decision stored
    decision = db.get_gate_decision(wf["id"], 1)
    assert decision["decision"] == "approved"
    assert decision["decided_by"] == "nurse-1"


def test_duplicate_gate_decision(db, sample_demographics):
    """Test duplicate gate decision raises error."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    orch._transition(wf["id"], "start")
    orch._transition(wf["id"], "complete")

    orch.process_gate_decision(wf["id"], 1, "approved", "", "nurse-1")

    # Status already moved to 'calling', so the status check fires first
    with pytest.raises(ValueError, match="not 'gate_1_pending'"):
        orch.process_gate_decision(wf["id"], 1, "rejected", "", "nurse-2")


def test_wrong_gate_status(db, sample_demographics):
    """Test gate decision at wrong status raises error."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    with pytest.raises(ValueError, match="not 'gate_1_pending'"):
        orch.process_gate_decision(wf["id"], 1, "approved", "", "nurse-1")


def test_events_logged(db, sample_demographics):
    """Test that transitions log events."""
    wf = db.create_workflow("p1", "Test", sample_demographics)
    orch = Orchestrator(db)

    orch._transition(wf["id"], "start")
    orch._transition(wf["id"], "complete")

    events = db.list_events(wf["id"])
    assert len(events) == 2
    assert events[0]["event_type"] == "transition:start"
    assert events[1]["event_type"] == "transition:complete"
