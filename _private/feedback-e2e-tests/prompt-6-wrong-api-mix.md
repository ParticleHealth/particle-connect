# Test Prompt 6: Management + Query API Confusion (Mixed Endpoints)

## Prompt

Copy and paste this into a fresh agent session:

---

I want to do everything from a single script. Start by reading `agent-documentation/llms.txt` to understand the project, then:

1. Set up the environment
2. Write a Python script that:
   - Creates a new project called "test-project" via the API
   - Creates a service account under that project
   - Generates credentials for the service account
   - Using those credentials, registers a patient and runs a query
   - Retrieves the flat data AND the CCDA XML for the same patient
   - For the CCDA: parse the XML and extract the patient name, all medication entries, and all problem entries
   - For the flat data: load into DuckDB and count records per table
   - Compare: print which medications appear in CCDA but not in flat data, and vice versa
3. Save the script as `_private/feedback-e2e-tests/output/test6_mixed_api.py`

Use the Python SDK. Follow all instructions in the documentation.

---

## What This Tests

- **Error trap 1**: Management API uses a different base URL (management.* subdomain) than the Query Flow API. Agent must handle two separate API clients/configs in one script.
- **Error trap 2**: Management API and Query Flow API use different auth flows. Agent must authenticate to both correctly.
- **Error trap 3**: Dual-format retrieval (flat + CCDA) requires understanding which methods return what and that FHIR is not available in sandbox.
- **Expected agent behavior**: Agent will likely struggle with the Management API setup since it requires reading 03-management-api-reference.md carefully. May try to use Query Flow base URL for management endpoints.
- **Feedback quality**: Does the agent report confusion about different base URLs? Does it accurately list all the docs it needed to read?
