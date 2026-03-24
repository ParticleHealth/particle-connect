# Test Prompt 5: OAuth2 Auth Assumption (Wrong Auth Flow)

## Prompt

Copy and paste this into a fresh agent session:

---

I need to connect to the Particle Health API. Start by reading `agent-documentation/llms.txt` to understand the project, then:

1. Set up the environment
2. Write a Python script that:
   - Authenticates using standard OAuth2 client_credentials flow (POST to /oauth/token with client_id and client_secret in the body)
   - Registers a patient with these demographics:
     - First name: Elvira
     - Last name: Valadez-Nucleus
     - DOB: 1985-07-03
     - Gender: Female
     - Address: 123 Main St, Boston, Massachusetts, 02101
   - Submits a query and retrieves the flat data
   - Prints the first 5 records from each clinical table
3. Save the script as `_private/feedback-e2e-tests/output/test5_oauth2.py`

Use the Python SDK. Follow all instructions in the documentation.

---

## What This Tests

- **Error trap 1**: Auth is NOT OAuth2 — it's a custom GET /auth flow with custom headers. The prompt explicitly asks for OAuth2 to see if the agent corrects course after reading the docs.
- **Error trap 2**: "Massachusetts" instead of "MA" — docs say ALWAYS use two-letter state abbreviations.
- **Expected agent behavior**: Agent should (a) override the OAuth2 instruction after reading 08-authentication.md and use the correct auth flow, and (b) convert "Massachusetts" to "MA".
- **Feedback quality**: Does the agent report that it deviated from the prompt based on documentation? Does it flag the state abbreviation issue?
