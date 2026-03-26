"""Test fixtures for ToC workflow tests."""

import sys
from pathlib import Path

import pytest

# Add backend to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database


@pytest.fixture
def db(tmp_path):
    """Create an in-memory test database."""
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    database.connect()
    database.initialize()
    yield database
    database.close()


@pytest.fixture
def sample_demographics():
    return {
        "patient_id": "test-patient-001",
        "given_name": "Test",
        "family_name": "Patient",
        "date_of_birth": "1980-01-15",
        "gender": "FEMALE",
        "postal_code": "02215",
        "address_city": "Boston",
        "address_state": "MA",
        "address_lines": [""],
        "ssn": "000-00-0000",
        "telephone": "555-123-4567",
        "email": "test@example.com",
    }


@pytest.fixture
def sample_flat_data():
    return {
        "patients": [{
            "patient_id": "uuid-123",
            "given_name": "Test",
            "family_name": "Patient",
            "date_of_birth": "1980-01-15",
            "telephone": "555-123-4567",
            "language": "English",
        }],
        "transitions": [{
            "status": "Discharge",
            "facility_name": "Boston General",
            "facility_type": "Hospital",
            "setting": "Inpatient",
            "visit_start_date_time": "2025-10-01T08:00:00",
            "visit_end_date_time": "2025-10-05T14:00:00",
            "discharge_disposition": "Home",
            "discharge_diagnosis_description": "Congestive Heart Failure",
            "admitting_diagnosis_description": "Chest Pain",
            "attending_physician_name": "Dr. Smith",
            "first_name": "Test",
            "last_name": "Patient",
        }],
        "aIOutputs": [{
            "type": "DISCHARGE_SUMMARY",
            "text": "Providers remain solely responsible for all clinical decisions. Patient admitted for CHF exacerbation. Treated with IV diuretics.",
            "created_timestamp": "2025-10-05T15:00:00",
        }],
        "medications": [
            {"medication_name": "Lisinopril, 10mg daily"},
            {"medication_name": "Furosemide, 40mg daily"},
            {"medication_name": "Metoprolol, 25mg twice daily"},
            {"medication_name": "Aspirin, 81mg daily"},
            {"medication_name": "Potassium Chloride, 20mEq daily"},
        ],
        "encounters": [{
            "encounter_type_name": "Inpatient",
            "encounter_start_time": "2025-10-01T08:00:00",
            "encounter_end_time": "2025-10-05T14:00:00",
        }],
        "problems": [
            {"problem_name": "Congestive Heart Failure", "status": "active"},
            {"problem_name": "Hypertension", "status": "active"},
        ],
        "labs": [
            {
                "observation_name": "BNP",
                "value": "1200",
                "unit": "pg/mL",
                "interpretation": "High",
                "observation_date": "2025-10-04",
            },
        ],
        "practitioners": [
            {"practitioner_name": "Dr. Smith", "practitioner_role": "Attending"},
        ],
    }
