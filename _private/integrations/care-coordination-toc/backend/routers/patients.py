"""Patient listing and data preview endpoints."""

from fastapi import APIRouter, Request

from config import DEMO_PATIENT

router = APIRouter(prefix="/api/patients", tags=["patients"])


DEMO_PATIENTS = [
    {
        "patient_id": DEMO_PATIENT["patient_id"],
        "name": f"{DEMO_PATIENT['given_name']} {DEMO_PATIENT['family_name']}",
        "date_of_birth": DEMO_PATIENT["date_of_birth"],
        "gender": DEMO_PATIENT["gender"],
        "city": DEMO_PATIENT["address_city"],
        "state": DEMO_PATIENT["address_state"],
    },
]


@router.get("")
async def list_patients(request: Request):
    db = request.app.state.db
    # Enrich with active workflow count
    result = []
    for p in DEMO_PATIENTS:
        workflows = db.list_workflows()
        active = [
            w for w in workflows
            if w["patient_id"] == p["patient_id"]
            and w["status"] not in ("completed", "cancelled", "failed")
        ]
        result.append({**p, "active_workflows": len(active)})
    return result
