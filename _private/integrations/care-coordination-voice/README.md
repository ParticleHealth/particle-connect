# Care Coordination Voice Demo

End-to-end demo: Particle flat data → AI discharge summary → automated voice follow-up call.

Simulates a care coordinator workflow where a voice agent calls a recently discharged patient to confirm their status, check on medications, and route to a disposition (follow-up call, appointment, or escalation).

## Architecture

```
Particle API (flat data)
  │
  ├── patients         → name, DOB, phone
  ├── transitions      → discharge facts (facility, diagnosis, disposition)
  ├── aIOutputs        → AI discharge summary (clinical narrative)
  ├── medications      → active med list
  └── encounters       → latest encounter context
  │
  ▼
call_context.py        → aggregates into structured call context
  │
  ▼
prompt_builder.py      → injects context into voice agent prompt
  │
  ▼
voice_client.py        → Retell AI: create agent + place outbound call
  │
  ▼
webhook_server.py      → receives disposition (followup / appointment / escalate)
```

## Setup

### 1. Retell AI account

1. Sign up at [retellai.com](https://www.retellai.com)
2. Get your API key from the dashboard
3. Buy or configure an outbound phone number

### 2. Environment variables

```bash
export RETELL_API_KEY="your-retell-api-key"
export RETELL_FROM_NUMBER="+12125551234"       # Your Retell phone number
export DEMO_OVERRIDE_PHONE="+12125559999"      # Your personal phone for testing
export WEBHOOK_URL="https://your-ngrok-url/call-events"
```

Particle sandbox credentials are built into `config.py` (same as particle-e2e).

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Data only (no voice call — good for verifying data aggregation)

```bash
python run_demo.py --data-only
```

This runs the Particle pipeline, builds the call context, and prints the generated voice agent prompt. No Retell account needed.

### Full demo with voice call

Terminal 1 — start the webhook server:
```bash
python webhook_server.py
```

Terminal 2 — expose webhooks via ngrok:
```bash
ngrok http 8000
# Copy the https URL and set WEBHOOK_URL
```

Terminal 3 — run the demo:
```bash
python run_demo.py
```

### Cached mode (skip Particle API calls)

After a successful first run, flat data is cached to `flat_data_cache.json`. Subsequent runs can skip the Particle API:

```bash
python run_demo.py --cached
python run_demo.py --cached --data-only
```

## Files

| File | Purpose |
|------|---------|
| `run_demo.py` | Main orchestrator — runs the full pipeline |
| `config.py` | Particle + Retell credentials and demo settings |
| `particle_client.py` | Particle API client (auth, register, query, flat data) |
| `call_context.py` | Aggregates flat data into voice agent call context |
| `prompt_builder.py` | Generates dynamic system prompt from call context |
| `voice_client.py` | Retell AI client (create agent, place call, get status) |
| `webhook_server.py` | Receives call completion events and dispositions |
| `requirements.txt` | Python dependencies |

## Voice Agent Conversation Flow

1. **Greeting & identity verification** — confirms patient by DOB
2. **Discharge status check** — "Are you currently home?"
3. **Contextual questions** — medication access, follow-up appointments, symptoms (informed by AI discharge summary)
4. **Disposition** — one of:
   - `schedule_followup_call` — patient is doing well, check again in N days
   - `schedule_appointment` — patient needs a provider visit
   - `escalate_to_coordinator` — red flag, needs human attention

## Swapping Voice Platforms

The voice integration is isolated to `voice_client.py`. To use Vapi instead of Retell:

1. Create `voice_client_vapi.py` implementing the same interface (`create_agent`, `create_call`, `get_call`, `delete_agent`)
2. Update the import in `run_demo.py`
3. Update `config.py` with Vapi credentials

The call context, prompt, and webhook handling are platform-agnostic.
