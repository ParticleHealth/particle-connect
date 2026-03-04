"""SQLite storage for Particle flat data."""

import sqlite3
import json
from config import DB_PATH


class ParticleDatabase:
    """Stores flat data in SQLite tables — one table per resource type."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def store_flat_data(self, flat_data: dict, patient_id: str):
        """Create tables dynamically from flat data and insert rows.

        Flat data structure: { "resourceType": [ {col: val, ...}, ... ], ... }
        All flat data values are TEXT per Particle docs.
        """
        cursor = self.conn.cursor()

        for resource_type, records in flat_data.items():
            if not isinstance(records, list) or len(records) == 0:
                print(f"  Skipping {resource_type}: no records")
                continue

            # Collect all columns across all records
            columns = set()
            for record in records:
                if isinstance(record, dict):
                    columns.update(record.keys())

            if not columns:
                continue

            # Sanitize table and column names
            table_name = _sanitize(resource_type)
            col_names = sorted(columns)
            safe_cols = [_sanitize(c) for c in col_names]

            # Add a patient_id tracking column
            all_cols = ["_patient_id"] + safe_cols
            col_defs = ", ".join(f'"{c}" TEXT' for c in all_cols)

            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

            # Insert rows
            placeholders = ", ".join(["?"] * len(all_cols))
            insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

            for record in records:
                if not isinstance(record, dict):
                    continue
                values = [patient_id] + [
                    _to_text(record.get(c)) for c in col_names
                ]
                cursor.execute(insert_sql, values)

            print(f"  Stored {len(records)} rows in table '{table_name}'")

        self.conn.commit()

    def query_problems(self, patient_id: str = None) -> list[dict]:
        """Query the problems table, optionally filtered by patient_id."""
        cursor = self.conn.cursor()

        # Check if problems table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='problems'"
        )
        if not cursor.fetchone():
            print("No 'problems' table found.")
            return []

        if patient_id:
            cursor.execute(
                'SELECT * FROM "problems" WHERE _patient_id = ?', (patient_id,)
            )
        else:
            cursor.execute('SELECT * FROM "problems"')

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def list_tables(self) -> list[str]:
        """List all tables in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cursor.fetchall()]

    def count_rows(self, table_name: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM "{_sanitize(table_name)}"')
        return cursor.fetchone()[0]

    def close(self):
        self.conn.close()


def _sanitize(name: str) -> str:
    """Remove characters that aren't safe for SQLite identifiers."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def _to_text(value) -> str | None:
    """Convert a value to text for storage. Handles nested objects."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)
