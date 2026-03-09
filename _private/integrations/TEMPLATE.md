# Integration: {CLIENT_NAME}

> Status: DISCOVERY | SPECIFICATION | DEVELOPMENT | TESTING | PRODUCTION

---

## Phase 1: Discovery (fill first)

### Client System
- **System name**:
- **System type**: EHR | Data Warehouse | Care Management | Population Health | Payer | Custom App | Other
- **Client technical contact**:

### What Data Do They Need from Particle?

| Need | Format | Particle Support |
|------|--------|-----------------|
| Patient demographics | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Lab results | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Medications | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Problems/Conditions | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Encounters | flat / CCDA / FHIR | flat (sandbox+prod), CCDA (sandbox+prod), FHIR (prod only) |
| Real-time ADT alerts | Signal webhooks | CloudEvents 1.0, sandbox trigger available |
| Other: | | |

### Data Direction
- [ ] Particle → Client (query + retrieve)
- [ ] Client → Particle (document submission)
- [ ] Bidirectional
- [ ] Real-time events (Signal webhooks)

### Volume and Frequency
- **Patient volume**: ___ patients (one-time backfill? ongoing?)
- **Query frequency**: One-time | Nightly batch | On-demand | Real-time triggers
- **Expected data size per patient**: Small (<100 records) | Medium (100-1K) | Large (1K+)

### Timeline
- **Target go-live**:
- **Sandbox access needed by**:
- **Production access needed by**:

### Known Unknowns
> List what you DON'T know yet. Flag who owns the answer.

| Question | Owner (Us / Client) | Status |
|----------|-------------------|--------|
| | | |
| | | |

---

## Phase 2: Specification (fill after discovery call)

### Data Flow Diagram

```
┌──────────────────┐         ┌────────────────────┐         ┌──────────────────┐
│  Client System   │         │  Integration Layer  │         │  Particle Health │
│                  │◄────────│                     │────────►│                  │
│  {system_name}   │         │  {middleware_type}   │         │  Query Flow API  │
│                  │ {transport_out} │              │ HTTPS    │  Signal API      │
└──────────────────┘         └────────────────────┘         └──────────────────┘
```

- **Integration layer**: Direct SDK | Custom middleware | ETL pipeline | Webhook relay | Other
- **Client-side transport**: REST API | Database insert | File drop (SFTP/S3) | Message queue | Webhook | Other
- **Error handling**: Retry on client side? Dead letter queue? Alert on failure?

### Client Auth Model
- **How we authenticate to client**: OAuth2 | API key | mTLS | Basic auth | SSH key | None (file drop)
- **Client endpoint URL**:
- **Auth credentials location**: (env var names, vault path — NEVER paste actual secrets here)
- **Rate limits on client side**:

### Particle Auth
- **Credential level**: Project (service account) | Organization
- **Environment**: Sandbox | Production
- **Scope ID**: projects/{id}
- **Credential storage**: .env | Vault | Cloud secret manager

### Data Mapping

> Map Particle fields to client's expected field names/formats.

#### Patient Demographics
| Particle Field | Client Field | Transform |
|---------------|-------------|-----------|
| given_name | | |
| family_name | | |
| date_of_birth | | Format: YYYY-MM-DD → ? |
| gender | | MALE/FEMALE → ? |
| address_state | | Two-letter abbreviation |
| postal_code | | 5 or 9 digit |

#### Clinical Data (add rows per resource type needed)
| Particle Resource | Particle Field | Client Field | Transform |
|------------------|---------------|-------------|-----------|
| medications | medication_name | | |
| labs | lab_name | | |
| labs | lab_value | | TEXT → numeric? |
| problems | condition_name | | |
| | | | |

### Compliance
- [ ] BAA in place
- [ ] HIPAA requirements reviewed
- [ ] State-specific rules (which states?):
- [ ] PHI logging restrictions understood (SDK redacts by default)
- [ ] Data retention policy agreed

### Particle Compatibility Check

> Review each item. Mark issues.

| Requirement | Compatible? | Notes |
|-------------|------------|-------|
| Data format available in target environment | | FHIR is prod-only |
| Volume within Particle rate limits | | |
| Query timing acceptable (2-5 min per patient) | | |
| Client can receive webhooks (if Signal needed) | | Needs public HTTPS endpoint |
| Client patient IDs can serve as Particle patient_id | | Must be stable + unique |

---

## Test Scenario Mapping

> Map client test cases to Particle sandbox patients and expected results.

| Test Case | Particle Test Patient | Expected Outcome |
|-----------|----------------------|-----------------|
| Basic data retrieval | Elvira Valadez-Nucleus (DOB: 1970-12-26, Boston MA) | 1,187 records across 16 resource types in flat |
| Empty data handling | Any arbitrary demographics | Query completes, flat returns `{}` |
| CCDA retrieval | Elvira Valadez-Nucleus | ZIP file with CCDA XML docs |
| Signal ADT alert | Elvira Valadez-Nucleus + ADMIT_TRANSITION_ALERT | CloudEvents webhook to callback_url |
| Re-registration (idempotent) | Same patient_id + same demographics | Returns same particle_patient_id |
| Re-registration (overlay error) | Same patient_id + different demographics | 422 overlay error |
| | | |

---

## Implementation Notes

> Add notes as development progresses. Reference specific files/commits.

-
