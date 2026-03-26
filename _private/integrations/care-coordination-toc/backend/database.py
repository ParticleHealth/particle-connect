"""SQLite database for workflow state persistence."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    patient_name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    current_step TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error_message TEXT,
    patient_demographics_json TEXT
);

CREATE TABLE IF NOT EXISTS patient_contexts (
    workflow_id TEXT PRIMARY KEY REFERENCES workflows(id),
    context_json TEXT NOT NULL,
    care_gaps_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS call_results (
    workflow_id TEXT PRIMARY KEY REFERENCES workflows(id),
    call_id TEXT,
    status TEXT,
    duration_ms INTEGER,
    transcript TEXT,
    disposition_action TEXT,
    disposition_params_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_records (
    workflow_id TEXT PRIMARY KEY REFERENCES workflows(id),
    recipient_email TEXT,
    subject TEXT,
    body_html TEXT,
    body_text TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    sent_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_decisions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    gate_number INTEGER NOT NULL,
    decision TEXT NOT NULL,
    coordinator_notes TEXT,
    decided_by TEXT,
    decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    event_type TEXT NOT NULL,
    event_data_json TEXT,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def initialize(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    # --- Workflows ---

    def create_workflow(self, patient_id: str, patient_name: str, demographics: dict) -> dict:
        wf_id = str(uuid.uuid4())
        now = _now()
        self.conn.execute(
            """INSERT INTO workflows (id, patient_id, patient_name, status, current_step, created_at, updated_at, patient_demographics_json)
               VALUES (?, ?, ?, 'pending', 'pending', ?, ?, ?)""",
            (wf_id, patient_id, patient_name, now, now, json.dumps(demographics)),
        )
        self.conn.commit()
        return self.get_workflow(wf_id)

    def get_workflow(self, workflow_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        return dict(row) if row else None

    def list_workflows(self, status: str | None = None, limit: int = 50) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM workflows WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM workflows ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_workflow_status(self, workflow_id: str, status: str, current_step: str, error_message: str | None = None):
        self.conn.execute(
            "UPDATE workflows SET status = ?, current_step = ?, updated_at = ?, error_message = ? WHERE id = ?",
            (status, current_step, _now(), error_message, workflow_id),
        )
        self.conn.commit()

    # --- Patient contexts ---

    def store_patient_context(self, workflow_id: str, context: dict, care_gaps: list[dict]):
        now = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO patient_contexts (workflow_id, context_json, care_gaps_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (workflow_id, json.dumps(context), json.dumps(care_gaps), now),
        )
        self.conn.commit()

    def get_patient_context(self, workflow_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM patient_contexts WHERE workflow_id = ?", (workflow_id,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["context"] = json.loads(result.pop("context_json"))
        result["care_gaps"] = json.loads(result.pop("care_gaps_json") or "[]")
        return result

    # --- Call results ---

    def store_call_result(
        self, workflow_id: str, call_id: str | None, status: str,
        duration_ms: int | None, transcript: str | None,
        disposition_action: str | None, disposition_params: dict | None,
    ):
        now = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO call_results
               (workflow_id, call_id, status, duration_ms, transcript, disposition_action, disposition_params_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (workflow_id, call_id, status, duration_ms, transcript,
             disposition_action, json.dumps(disposition_params) if disposition_params else None, now),
        )
        self.conn.commit()

    def get_call_result(self, workflow_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM call_results WHERE workflow_id = ?", (workflow_id,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        params = result.pop("disposition_params_json", None)
        result["disposition_params"] = json.loads(params) if params else None
        return result

    # --- Email records ---

    def store_email_record(
        self, workflow_id: str, recipient_email: str | None, subject: str,
        body_html: str, body_text: str, status: str,
    ):
        now = _now()
        self.conn.execute(
            """INSERT OR REPLACE INTO email_records
               (workflow_id, recipient_email, subject, body_html, body_text, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (workflow_id, recipient_email, subject, body_html, body_text, status, now),
        )
        self.conn.commit()

    def update_email_status(self, workflow_id: str, status: str):
        self.conn.execute(
            "UPDATE email_records SET status = ?, sent_at = ? WHERE workflow_id = ?",
            (status, _now() if status == "sent" else None, workflow_id),
        )
        self.conn.commit()

    def get_email_record(self, workflow_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM email_records WHERE workflow_id = ?", (workflow_id,)
        ).fetchone()
        return dict(row) if row else None

    # --- Gate decisions ---

    def store_gate_decision(
        self, workflow_id: str, gate_number: int, decision: str,
        coordinator_notes: str, decided_by: str,
    ):
        decision_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO gate_decisions (id, workflow_id, gate_number, decision, coordinator_notes, decided_by, decided_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (decision_id, workflow_id, gate_number, decision, coordinator_notes, decided_by, _now()),
        )
        self.conn.commit()

    def get_gate_decision(self, workflow_id: str, gate_number: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM gate_decisions WHERE workflow_id = ? AND gate_number = ?",
            (workflow_id, gate_number),
        ).fetchone()
        return dict(row) if row else None

    def list_gate_decisions(self, workflow_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM gate_decisions WHERE workflow_id = ? ORDER BY gate_number",
            (workflow_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Workflow events ---

    def log_event(self, workflow_id: str, event_type: str, event_data: dict | None = None):
        self.conn.execute(
            """INSERT INTO workflow_events (workflow_id, event_type, event_data_json, created_at)
               VALUES (?, ?, ?, ?)""",
            (workflow_id, event_type, json.dumps(event_data) if event_data else None, _now()),
        )
        self.conn.commit()

    def list_events(self, workflow_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM workflow_events WHERE workflow_id = ? ORDER BY created_at",
            (workflow_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            data = d.pop("event_data_json", None)
            d["event_data"] = json.loads(data) if data else None
            results.append(d)
        return results
