# Test Prompt 3: Bi-Directional Document Submission Round-Trip

## Prompt

Copy and paste this into a fresh agent session:

---

I want to test Particle's bi-directional document submission — sending a C-CDA XML document TO Particle and then retrieving it back. Start by reading `agent-documentation/llms.txt` to understand the project, then:

1. Set up the environment
2. Write a complete Python script that:
   - Authenticates with the sandbox API
   - Creates or uses a minimal valid C-CDA XML document (use an example from the docs or generate one)
   - Submits the document via the Documents API (POST /api/v1/documents) with the correct headers and external patient_id
   - Lists documents to confirm submission
   - Retrieves the submitted document back
   - Compares the submitted vs retrieved document and prints a diff summary
3. Include proper error handling for common failure cases
4. Save the script as `_private/feedback-e2e-tests/output/test3_bidirectional.py`

Use the Python SDK where possible. Follow all instructions in the documentation.

---

## What This Tests

- **Feedback trigger**: Requires reading the most docs (terminology, SDK, auth, bidirectionality, data models, API reference). Higher chance of hitting doc gaps between v1/v2 endpoint confusion.
- **Doc discovery**: Agent must read llms.txt, 00-terminology.md, 02-api-reference.md, 04-sdk-reference.md, 08-authentication.md, 13-bidirectionality.md
- **Breadth of feedback**: Does the agent report which docs it read? Does it flag confusion between v1 Documents API and v2 Query Flow API?
