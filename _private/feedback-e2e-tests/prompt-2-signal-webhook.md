# Test Prompt 2: Signal/ADT Webhook Receiver

## Prompt

Copy and paste this into a fresh agent session:

---

I need to build a real-time patient alert system using Particle's Signal/ADT webhooks. Start by reading `agent-documentation/llms.txt` to understand the project, then:

1. Set up the environment
2. Write a complete Python script that:
   - Registers the sandbox test patient
   - Subscribes the patient to MONITORING via Signal
   - Stands up a local FastAPI webhook receiver on port 8080
   - Triggers an ADMIT_TRANSITION_ALERT using the sandbox trigger endpoint
   - Receives the CloudEvents webhook, verifies the HMAC signature, and parses the payload
   - Prints the parsed alert details (event type, patient, facility, timestamp)
3. Save the script as `_private/feedback-e2e-tests/output/test2_signal_webhook.py`

Use the Python SDK where possible. Follow all instructions in the documentation.

---

## What This Tests

- **Feedback trigger**: Likely to hit issues — Signal subscribe 400 handling, trigger-sandbox-workflow plain text response, HMAC verification details. Agent should report `outcome: partial` with error details.
- **Doc discovery**: Agent must read llms.txt, 02-api-reference.md (Signal section), 04-sdk-reference.md, 12-notification-data-contract.md
- **Error reporting quality**: Does the agent accurately describe what went wrong and which doc was unclear?
