"""Aggregates Particle flat data into a structured context for agents.

Extended from care-coordination-voice/call_context.py with additional
data extraction for problems, labs, practitioners, and care gap analysis.
"""


def build_call_context(flat_data: dict, patient_id: str) -> dict:
    """Build a structured call context from raw flat data."""
    patients = flat_data.get("patients", [])
    patient = patients[0] if patients else {}

    transitions = flat_data.get("transitions", [])
    discharge = _latest_by_field(
        [t for t in transitions if (t.get("status") or "").lower() == "discharge"],
        "visit_end_date_time",
    )

    ai_outputs = flat_data.get("aIOutputs", [])
    ai_summary = _latest_by_field(
        [o for o in ai_outputs if o.get("type") == "DISCHARGE_SUMMARY"],
        "created_timestamp",
    )

    medications = flat_data.get("medications", [])
    active_meds = _deduplicate_medications(medications)

    encounters = flat_data.get("encounters", [])
    latest_encounter = _latest_by_field(encounters, "encounter_end_time")

    problems = flat_data.get("problems", [])
    labs = flat_data.get("labs", [])
    practitioners = flat_data.get("practitioners", [])

    phone = None
    if discharge:
        phone = discharge.get("phone_number")
    if not phone:
        phone = patient.get("telephone")

    first_name = ""
    last_name = ""
    if discharge and discharge.get("first_name"):
        first_name = discharge["first_name"]
        last_name = discharge.get("last_name", "")
    else:
        first_name = _first_name(patient.get("given_name", ""))
        last_name = patient.get("family_name", "")

    dob = patient.get("date_of_birth", "")
    if not dob and discharge:
        dob = discharge.get("dob", "")
    dob = _format_date(dob)

    return {
        "patient_id": patient_id,
        "patient_first_name": first_name,
        "patient_last_name": last_name,
        "patient_dob": dob,
        "phone_number": phone,
        "language": patient.get("language", "English"),

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

        "ai_discharge_summary": _strip_disclaimer(
            ai_summary.get("text", "") if ai_summary else ""
        ),

        "active_medications": active_meds,

        "encounter_type": _get(latest_encounter, "encounter_type_name"),
        "encounter_start": _get(latest_encounter, "encounter_start_time"),
        "encounter_end": _get(latest_encounter, "encounter_end_time"),

        # Extended fields for ToC workflow
        "problems": _extract_problems(problems),
        "recent_labs": _extract_recent_labs(labs),
        "care_team": _extract_care_team(practitioners),
    }


def analyze_care_gaps(context: dict, flat_data: dict) -> list[dict]:
    """Identify care gaps from patient context and flat data."""
    gaps = []

    # High-risk diagnoses without evident care plan
    high_risk_keywords = ["heart failure", "chf", "copd", "sepsis", "pneumonia", "stroke"]
    diagnosis = (context.get("discharge_diagnosis") or "").lower()
    for keyword in high_risk_keywords:
        if keyword in diagnosis:
            gaps.append({
                "type": "high_risk_diagnosis",
                "severity": "high",
                "detail": f"High-risk diagnosis: {context['discharge_diagnosis']}",
            })
            break

    # Missing follow-up: no encounter after discharge
    if context.get("discharge_date") and context["discharge_date"] != "Unknown":
        encounters = flat_data.get("encounters", [])
        post_discharge = [
            e for e in encounters
            if (e.get("encounter_start_time") or "") > context["discharge_date"]
        ]
        if not post_discharge:
            gaps.append({
                "type": "missing_followup",
                "severity": "medium",
                "detail": "No follow-up encounter found after discharge",
            })

    # Medication reconciliation: many active meds
    med_count = len(context.get("active_medications", []))
    if med_count >= 5:
        gaps.append({
            "type": "med_reconciliation",
            "severity": "medium",
            "detail": f"{med_count} active medications — reconciliation recommended",
        })

    # Abnormal labs
    for lab in context.get("recent_labs", []):
        if lab.get("flag") and lab["flag"].lower() in ("abnormal", "high", "low", "critical"):
            gaps.append({
                "type": "abnormal_lab",
                "severity": "high" if lab["flag"].lower() == "critical" else "medium",
                "detail": f"Abnormal lab: {lab.get('name', 'Unknown')} — {lab.get('flag')}",
            })

    return gaps


# --- Extended extractors ---

def _extract_problems(problems: list[dict]) -> list[dict]:
    """Extract active problems with deduplication."""
    seen = set()
    result = []
    for p in problems:
        name = p.get("problem_name") or p.get("description") or ""
        if not name:
            continue
        key = name.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append({
                "name": name,
                "status": p.get("status", ""),
                "onset_date": p.get("onset_date", ""),
            })
    return result


def _extract_recent_labs(labs: list[dict], max_results: int = 20) -> list[dict]:
    """Extract recent lab results sorted by date."""
    dated = [l for l in labs if l.get("observation_date")]
    dated.sort(key=lambda l: l["observation_date"], reverse=True)
    result = []
    for l in dated[:max_results]:
        result.append({
            "name": l.get("observation_name", ""),
            "value": l.get("value", ""),
            "unit": l.get("unit", ""),
            "flag": l.get("interpretation", ""),
            "date": _format_date(l.get("observation_date", "")),
        })
    return result


def _extract_care_team(practitioners: list[dict]) -> list[dict]:
    """Extract unique care team members."""
    seen = set()
    result = []
    for p in practitioners:
        name = p.get("practitioner_name", "")
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        result.append({
            "name": name,
            "role": p.get("practitioner_role", ""),
            "specialty": p.get("specialty", ""),
        })
    return result


# --- Helpers (from care-coordination-voice) ---

def _latest_by_field(records: list[dict], field: str) -> dict | None:
    dated = [r for r in records if r.get(field)]
    if not dated:
        return records[0] if records else None
    return max(dated, key=lambda r: r[field])


def _deduplicate_medications(medications: list[dict]) -> list[str]:
    seen = set()
    unique = []
    for m in medications:
        name = m.get("medication_name", "")
        if not name:
            continue
        base = name.split(",")[0].strip()
        if base.lower() not in seen:
            seen.add(base.lower())
            unique.append(base)
    return sorted(unique)


def _first_name(given_name: str) -> str:
    return given_name.split(",")[0].strip() if given_name else ""


def _get(record: dict | None, field: str, default: str = "Unknown") -> str:
    if record is None:
        return default
    return record.get(field) or default


def _format_date(value: str) -> str:
    if not value or value == "Unknown":
        return value
    for sep in ("T", " "):
        if sep in value:
            return value.split(sep)[0]
    return value


def _strip_disclaimer(text: str) -> str:
    marker = "responsible for all clinical decisions."
    idx = text.find(marker)
    if idx != -1:
        text = text[idx + len(marker):].strip()
    return text
