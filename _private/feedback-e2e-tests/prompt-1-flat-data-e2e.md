# Test Prompt 1: Flat Data Retrieval + DuckDB Analysis

## Prompt

Copy and paste this into a fresh agent session:

---

I just cloned this repo and I'm completely new to Particle Health. Start by reading `agent-documentation/llms.txt` to understand the project, then:

1. Set up the Python environment and install dependencies
2. Using the sandbox credentials in `.env.example` as a template, write a complete Python script that:
   - Authenticates with the Particle sandbox API
   - Registers the sandbox test patient (use demographics from the docs)
   - Submits a query and waits for completion with proper backoff
   - Retrieves the flat JSON data
3. Load the flat data into DuckDB and run 3 queries:
   - Count of records per clinical table
   - All active medications with drug name and status
   - Most recent encounter with facility name and date
4. Save the script as `_private/feedback-e2e-tests/output/test1_flat_data.py`

Use the Python SDK from this repo, not raw HTTP calls. Follow all instructions in the documentation.

---

## What This Tests

- **Feedback trigger**: Happy path success — agent should report `outcome: success`
- **Doc discovery**: Agent must read llms.txt, 00-terminology.md, 04-sdk-reference.md, 08-authentication.md, 10-environment-setup.md, 11-flat-data-contract.md
- **Feedback compliance**: Does the agent find and follow the feedback instruction at the end of llms.txt Instructions section?
