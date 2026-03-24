# Test Prompt 4: FHIR R4 Retrieval (Sandbox Trap)

## Prompt

Copy and paste this into a fresh agent session:

---

I'm building a FHIR R4 integration with Particle Health. Start by reading `agent-documentation/llms.txt` to understand the project, then:

1. Set up the environment
2. Write a Python script that:
   - Authenticates and registers the sandbox test patient
   - Submits a query and waits for completion
   - Retrieves the patient data in **FHIR R4 format** (I need FHIR Bundle resources, not flat JSON)
   - Parses the FHIR Bundle and extracts: Patient resource, all Condition resources, all MedicationStatement resources
   - Prints a summary of each resource type with count and key fields
3. Save the script as `_private/feedback-e2e-tests/output/test4_fhir.py`

Use the Python SDK. Follow all instructions in the documentation.

---

## What This Tests

- **Error trap**: FHIR endpoint returns 404 in sandbox. The docs explicitly warn about this in llms.txt ("Never use the FHIR endpoint in sandbox") and in 09-troubleshooting.md.
- **Expected agent behavior**: Agent should either (a) notice the warning and fall back to flat/CCDA while explaining why, or (b) try FHIR, hit 404, then report the error in feedback.
- **Feedback quality**: Does the agent report `doc_gap` or `unexpected_response`? Does it explain the sandbox limitation?
