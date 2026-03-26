#!/usr/bin/env python3
"""Care Coordination Voice Demo — end-to-end discharge follow-up call.

Pipeline:
  1. Authenticate with Particle sandbox
  2. Register patient + submit query + wait for data
  3. Retrieve flat data
  4. Aggregate into call context (demographics, discharge summary, meds)
  5. Build dynamic voice agent prompt
  6. Create Retell agent + initiate outbound call
  7. Poll for call completion + print results

Prerequisites:
  - RETELL_API_KEY env var set
  - RETELL_FROM_NUMBER env var set (your Retell phone number)
  - DEMO_OVERRIDE_PHONE env var set (your phone number for testing)
  - webhook_server.py running (with ngrok for Retell webhooks)

Usage:
    # Full pipeline: Particle API → flat data → voice call
    python run_demo.py

    # Skip Particle API calls, use cached flat data from a previous run
    python run_demo.py --cached

    # Data only: pull flat data and show call context, no voice call
    python run_demo.py --data-only
"""

import argparse
import json
import sys
import time

from config import DEMO_PATIENT, DEMO_OVERRIDE_PHONE
from particle_client import ParticleClient
from call_context import build_call_context, print_call_context
from prompt_builder import build_prompt
from voice_client import RetellVoiceClient


FLAT_DATA_CACHE = "flat_data_cache.json"


def fetch_flat_data() -> tuple[str, dict]:
    """Run the Particle pipeline: auth → register → query → flat data."""
    client = ParticleClient()
    try:
        print("=" * 60)
        print("STEP 1: PARTICLE API — FETCH FLAT DATA")
        print("=" * 60)

        print("Authenticating...")
        client.authenticate()
        print("  OK")

        print(f"Registering patient: "
              f"{DEMO_PATIENT['given_name']} {DEMO_PATIENT['family_name']}...")
        resp = client.register_patient(DEMO_PATIENT)
        patient_id = resp.get("particle_patient_id")
        if not patient_id:
            print(f"ERROR: No patient ID. Response: {json.dumps(resp, indent=2)}")
            sys.exit(1)
        print(f"  Patient ID: {patient_id}")

        print("Submitting query...")
        client.submit_query(patient_id)
        print("Waiting for query completion...")
        result = client.wait_for_query(patient_id)
        status = result.get("state", result.get("status", "UNKNOWN"))
        if status == "FAILED":
            print(f"ERROR: Query failed. {json.dumps(result, indent=2)}")
            sys.exit(1)
        print(f"  Query status: {status}")

        print("Retrieving flat data...")
        flat_data = client.get_flat_data(patient_id)
        resource_types = list(flat_data.keys()) if isinstance(flat_data, dict) else []
        print(f"  Resource types: {len(resource_types)}")
        for rt in resource_types:
            count = len(flat_data[rt]) if isinstance(flat_data[rt], list) else 0
            print(f"    {rt}: {count} records")

        # Cache for --cached mode
        with open(FLAT_DATA_CACHE, "w") as f:
            json.dump({"patient_id": patient_id, "flat_data": flat_data}, f, indent=2)
        print(f"  Cached to {FLAT_DATA_CACHE}")

        return patient_id, flat_data

    finally:
        client.close()


def load_cached_flat_data() -> tuple[str, dict]:
    """Load flat data from a previous run."""
    print("Loading cached flat data...")
    try:
        with open(FLAT_DATA_CACHE) as f:
            cached = json.load(f)
        patient_id = cached["patient_id"]
        flat_data = cached["flat_data"]
        print(f"  Patient ID: {patient_id}")
        print(f"  Resource types: {len(flat_data)}")
        return patient_id, flat_data
    except FileNotFoundError:
        print(f"ERROR: No cached data at {FLAT_DATA_CACHE}. Run without --cached first.")
        sys.exit(1)


def initiate_voice_call(call_context: dict, prompt: str) -> dict:
    """Create a Retell agent and place the outbound call."""
    print("=" * 60)
    print("STEP 3: VOICE CALL — RETELL AI")
    print("=" * 60)

    voice = RetellVoiceClient()
    agent = None
    try:
        # Determine phone number
        phone = DEMO_OVERRIDE_PHONE or call_context["phone_number"]
        if not phone:
            print("ERROR: No phone number available.")
            print("  Set DEMO_OVERRIDE_PHONE env var for testing.")
            sys.exit(1)

        # Normalize to E.164 if needed
        phone = _normalize_phone(phone)
        print(f"  Calling: {phone}")

        # Create agent with patient-specific prompt
        print("Creating voice agent...")
        agent = voice.create_agent(prompt)
        agent_id = agent["agent_id"]

        # Place the call
        print("Initiating outbound call...")
        call = voice.create_call(
            agent_id=agent_id,
            to_number=phone,
            metadata={
                "patient_id": call_context["patient_id"],
                "patient_name": (
                    f"{call_context['patient_first_name']} "
                    f"{call_context['patient_last_name']}"
                ),
                "facility": call_context["facility_name"],
            },
        )
        call_id = call["call_id"]

        # Poll for completion
        print("\nCall in progress. Waiting for completion...")
        print("(Disposition will appear in webhook_server.py output)\n")
        _poll_call_status(voice, call_id)

        # Retrieve final call details
        final = voice.get_call(call_id)

        # Clean up the agent + LLM after the call is done
        print("\nCleaning up Retell resources...")
        try:
            voice.delete_agent(agent["agent_id"], agent.get("llm_id"))
        except Exception:
            pass

        return final

    except Exception:
        # Clean up on error too
        if agent:
            try:
                voice.delete_agent(agent["agent_id"], agent.get("llm_id"))
            except Exception:
                pass
        raise
    finally:
        voice.close()


def _poll_call_status(voice: RetellVoiceClient, call_id: str, timeout: int = 360):
    """Poll call status until it ends."""
    elapsed = 0
    while elapsed < timeout:
        try:
            call = voice.get_call(call_id)
            status = call.get("call_status", "unknown")
            if status in ("ended", "error"):
                duration = call.get("call_duration_ms", 0)
                print(f"  Call ended. Duration: {duration / 1000:.1f}s")
                print(f"  End reason: {call.get('end_call_reason', 'unknown')}")

                # Print transcript if available
                transcript = call.get("transcript", "")
                if transcript:
                    print("\n  TRANSCRIPT:")
                    print("  " + "-" * 56)
                    for line in transcript.split("\n"):
                        print(f"  {line}")
                    print("  " + "-" * 56)

                # Print tool calls (dispositions)
                tool_calls = call.get("tool_calls", [])
                if tool_calls:
                    print("\n  DISPOSITION:")
                    for tc in tool_calls:
                        print(f"    {tc.get('name')}: {json.dumps(tc.get('arguments', {}))}")

                return
            print(f"  [{elapsed}s] Call status: {status}")
        except Exception as e:
            print(f"  [{elapsed}s] Poll error: {e}")

        time.sleep(5)
        elapsed += 5

    print(f"  Call polling timed out after {timeout}s")


def _normalize_phone(phone: str) -> str:
    """Normalize phone to E.164 format (+1XXXXXXXXXX)."""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return phone  # Return as-is if already formatted or international


def main():
    parser = argparse.ArgumentParser(
        description="Care coordination voice demo: Particle flat data → voice call"
    )
    parser.add_argument(
        "--cached", action="store_true",
        help="Use cached flat data from a previous run (skip Particle API calls)",
    )
    parser.add_argument(
        "--data-only", action="store_true",
        help="Fetch and display call context only — don't place a voice call",
    )
    args = parser.parse_args()

    # Step 1: Get flat data
    if args.cached:
        patient_id, flat_data = load_cached_flat_data()
    else:
        patient_id, flat_data = fetch_flat_data()
    print()

    # Step 2: Aggregate into call context
    print("=" * 60)
    print("STEP 2: BUILD CALL CONTEXT")
    print("=" * 60)
    ctx = build_call_context(flat_data, patient_id)
    print_call_context(ctx)
    print()

    # Build the voice agent prompt
    prompt = build_prompt(ctx)

    if args.data_only:
        print("=" * 60)
        print("GENERATED PROMPT (for review)")
        print("=" * 60)
        print(prompt)
        print("\nDone. Run without --data-only to place the voice call.")
        return

    # Step 3: Place the voice call
    call_result = initiate_voice_call(ctx, prompt)

    # Done
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"  Patient: {ctx['patient_first_name']} {ctx['patient_last_name']}")
    print(f"  Facility: {ctx['facility_name']}")
    if call_result:
        d = call_result.get("tool_calls", [])
        if d:
            print(f"  Disposition: {d[0].get('name', 'unknown')}")
        else:
            print("  Disposition: (none — check webhook_server.py)")


if __name__ == "__main__":
    main()
