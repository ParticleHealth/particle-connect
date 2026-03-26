"""Aggregates Particle flat data into a call context for the voice agent.

Pulls from three flat data tables:
  - patients:     demographics, phone number
  - transitions:  discharge event facts (facility, diagnosis, disposition)
  - aIOutputs:    AI-generated discharge summary (rich clinical narrative)
  - medications:  active medication list for med reconciliation
  - encounters:   latest encounter metadata
"""


def build_call_context(flat_data: dict, patient_id: str) -> dict:
    """Build a structured call context from raw flat data.

    Returns a dict with everything the voice agent prompt needs:
    patient identity, discharge facts, clinical summary, and active meds.
    """
    # --- Patient demographics ---
    patients = flat_data.get("patients", [])
    patient = patients[0] if patients else {}

    # --- Latest discharge transition ---
    # Note: status is capitalized ("Discharge", not "discharge") in flat data.
    # Use visit_end_date_time for the actual discharge date (status_date_time
    # is when Particle ingested the record, not the clinical event).
    transitions = flat_data.get("transitions", [])
    discharge = _latest_by_field(
        [t for t in transitions if (t.get("status") or "").lower() == "discharge"],
        "visit_end_date_time",
    )

    # --- AI discharge summary (richest clinical context) ---
    ai_outputs = flat_data.get("aIOutputs", [])
    ai_summary = _latest_by_field(
        [o for o in ai_outputs if o.get("type") == "DISCHARGE_SUMMARY"],
        "created_timestamp",
    )

    # --- Active medications (deduplicated by base name) ---
    medications = flat_data.get("medications", [])
    active_meds = _deduplicate_medications(medications)

    # --- Latest encounter ---
    encounters = flat_data.get("encounters", [])
    latest_encounter = _latest_by_field(encounters, "encounter_end_time")

    # --- Assemble context ---
    # Phone number: prefer transitions, fall back to patients table
    phone = None
    if discharge:
        phone = discharge.get("phone_number")
    if not phone:
        phone = patient.get("telephone")

    # Patient name: prefer transitions (has first_name/last_name directly),
    # fall back to patients table (given_name/family_name)
    first_name = ""
    last_name = ""
    if discharge and discharge.get("first_name"):
        first_name = discharge["first_name"]
        last_name = discharge.get("last_name", "")
    else:
        first_name = _first_name(patient.get("given_name", ""))
        last_name = patient.get("family_name", "")

    # DOB: prefer patients table format, fall back to transitions
    dob = patient.get("date_of_birth", "")
    if not dob and discharge:
        dob = discharge.get("dob", "")
    # Clean up timestamp format for voice agent (just the date part)
    dob = _format_date(dob)

    return {
        "patient_id": patient_id,

        # Identity & contact
        "patient_first_name": first_name,
        "patient_last_name": last_name,
        "patient_dob": dob,
        "phone_number": phone,
        "language": patient.get("language", "English"),

        # Discharge facts (structured, from transitions table)
        "facility_name": _get(discharge, "facility_name"),
        "facility_type": _get(discharge, "facility_type"),
        "setting": _get(discharge, "setting"),
        "discharge_date": _format_date(_get(discharge, "visit_end_date_time")),
        "discharge_disposition": _get(discharge, "discharge_disposition"),
        "discharge_diagnosis": _get(discharge, "discharge_diagnosis_description"),
        "admitting_diagnosis": _get(discharge, "admitting_diagnosis_description"),
        "attending_physician": _get(discharge, "attending_physician_name"),
        "visit_start": _format_date(_get(discharge, "visit_start_date_time")),
        "visit_end": _format_date(_get(discharge, "visit_end_date_time")),

        # Rich clinical narrative (from AI summary)
        "ai_discharge_summary": _strip_disclaimer(
            ai_summary.get("text", "") if ai_summary else ""
        ),

        # Medication list for reconciliation questions
        "active_medications": active_meds,

        # Encounter metadata
        "encounter_type": _get(latest_encounter, "encounter_type_name"),
        "encounter_start": _get(latest_encounter, "encounter_start_time"),
        "encounter_end": _get(latest_encounter, "encounter_end_time"),
    }


def print_call_context(ctx: dict):
    """Pretty-print the call context for demo visibility."""
    print("=" * 60)
    print("CALL CONTEXT")
    print("=" * 60)
    print(f"  Patient:    {ctx['patient_first_name']} {ctx['patient_last_name']}")
    print(f"  DOB:        {ctx['patient_dob']}")
    print(f"  Phone:      {ctx['phone_number']}")
    print(f"  Language:   {ctx['language']}")
    print()
    print(f"  Facility:    {ctx['facility_name']} ({ctx.get('setting', 'Unknown')})")
    print(f"  Admitted:    {ctx['visit_start']}")
    print(f"  Discharged:  {ctx['discharge_date']}")
    print(f"  Disposition: {ctx['discharge_disposition']}")
    print(f"  Diagnosis:   {ctx['discharge_diagnosis']}")
    print(f"  Attending:   {ctx['attending_physician']}")
    print()
    print(f"  Active medications ({len(ctx['active_medications'])}):")
    for med in ctx["active_medications"][:10]:
        # Truncate long med names for display
        display = med[:70] + "..." if len(med) > 70 else med
        print(f"    - {display}")
    if len(ctx["active_medications"]) > 10:
        print(f"    ... and {len(ctx['active_medications']) - 10} more")
    print()
    summary = ctx["ai_discharge_summary"]
    if summary:
        preview = summary[:300] + "..." if len(summary) > 300 else summary
        print(f"  AI Summary (preview):\n    {preview}")
    else:
        print("  AI Summary: (none available)")
    print("=" * 60)


# --- Helpers ---

def _latest_by_field(records: list[dict], field: str) -> dict | None:
    """Return the record with the most recent value for a given field."""
    dated = [r for r in records if r.get(field)]
    if not dated:
        return records[0] if records else None
    return max(dated, key=lambda r: r[field])


def _deduplicate_medications(medications: list[dict]) -> list[str]:
    """Deduplicate medications by base name (before the first comma).

    Flat data often has many records for the same drug (different encounters,
    statement periods, etc.). We want unique drug names for the voice prompt.
    """
    seen = set()
    unique = []
    for m in medications:
        name = m.get("medication_name", "")
        if not name:
            continue
        # Use the base name (first segment before comma) as dedup key
        base = name.split(",")[0].strip()
        if base.lower() not in seen:
            seen.add(base.lower())
            unique.append(base)
    return sorted(unique)


def _first_name(given_name: str) -> str:
    """Extract first name from comma-delimited given_name field."""
    return given_name.split(",")[0].strip() if given_name else ""


def _get(record: dict | None, field: str, default: str = "Unknown") -> str:
    """Safe get from a possibly-None record."""
    if record is None:
        return default
    return record.get(field) or default


def _format_date(value: str) -> str:
    """Extract just the date portion from a timestamp string.

    Turns '1970-12-26T00:00:00' or '2025-11-01 23:30:00.000000+00:00'
    into '1970-12-26'. Returns the original value if parsing fails.
    """
    if not value or value == "Unknown":
        return value
    # Handle both 'T' separator and space separator
    for sep in ("T", " "):
        if sep in value:
            return value.split(sep)[0]
    return value


def _strip_disclaimer(text: str) -> str:
    """Strip the AI disclaimer block from the beginning of a summary.

    Particle AI summaries start with a standard disclaimer paragraph ending
    with "Providers remain solely responsible for all clinical decisions."
    """
    marker = "responsible for all clinical decisions."
    idx = text.find(marker)
    if idx != -1:
        text = text[idx + len(marker):].strip()
    return text
