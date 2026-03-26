"""Webhook server for receiving Retell call events.

Handles call completion, tool call results (disposition), and transcripts.
Run this alongside run_demo.py to capture outcomes.

Usage:
    python webhook_server.py          # Start on port 8000
    ngrok http 8000                   # Expose for Retell webhooks (separate terminal)
"""

import json
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler


# In-memory store for demo — in production this would be a database
call_results = {}


class WebhookHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        event = json.loads(body)

        path = self.path
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        if path == "/call-events":
            self._handle_call_event(event, timestamp)
        else:
            print(f"[{timestamp}] Unknown webhook path: {path}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def _handle_call_event(self, event: dict, timestamp: str):
        """Process call status updates and tool call results from Retell."""
        event_type = event.get("event", "unknown")
        call_id = event.get("call", {}).get("call_id", "unknown")

        print(f"\n[{timestamp}] Event: {event_type} | Call: {call_id}")

        if event_type == "call_ended":
            call = event.get("call", {})
            self._handle_call_ended(call, timestamp)

        elif event_type == "call_analyzed":
            call = event.get("call", {})
            self._handle_call_analyzed(call, timestamp)

    def _handle_call_ended(self, call: dict, timestamp: str):
        """Handle call completion — extract disposition from tool calls."""
        call_id = call.get("call_id", "unknown")
        duration_ms = call.get("call_duration_ms", 0)
        end_reason = call.get("end_call_reason", "unknown")
        transcript = call.get("transcript", "")

        print(f"  Duration: {duration_ms / 1000:.1f}s")
        print(f"  End reason: {end_reason}")

        # Extract tool calls (disposition decisions)
        tool_calls = call.get("tool_calls", [])
        disposition = None
        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("arguments", {})
            print(f"  Tool call: {tool_name}({json.dumps(tool_args)})")

            if tool_name in (
                "schedule_followup_call",
                "schedule_appointment",
                "escalate_to_coordinator",
            ):
                disposition = {
                    "action": tool_name,
                    "parameters": tool_args,
                    "timestamp": timestamp,
                }

        # Store result
        result = {
            "call_id": call_id,
            "duration_ms": duration_ms,
            "end_reason": end_reason,
            "disposition": disposition,
            "transcript": transcript,
            "metadata": call.get("metadata", {}),
        }
        call_results[call_id] = result

        # Print disposition summary
        print()
        if disposition:
            action = disposition["action"]
            params = disposition["parameters"]
            if action == "schedule_followup_call":
                print(f"  DISPOSITION: Follow-up call in {params.get('days_from_now')} days")
                print(f"  Notes: {params.get('notes', '')}")
            elif action == "schedule_appointment":
                print(f"  DISPOSITION: Schedule appointment ({params.get('urgency')})")
                print(f"  Reason: {params.get('reason', '')}")
                print(f"  Provider: {params.get('provider_type', 'PCP')}")
            elif action == "escalate_to_coordinator":
                print(f"  DISPOSITION: ESCALATE ({params.get('priority', 'standard')})")
                print(f"  Reason: {params.get('reason', '')}")
        else:
            print("  DISPOSITION: None (call ended without tool call)")

    def _handle_call_analyzed(self, call: dict, timestamp: str):
        """Handle post-call analysis (sentiment, summary) if enabled."""
        call_id = call.get("call_id", "unknown")
        analysis = call.get("call_analysis", {})
        if analysis:
            print(f"  Analysis for {call_id}:")
            print(f"    Sentiment: {analysis.get('user_sentiment', 'unknown')}")
            print(f"    Summary: {analysis.get('call_summary', 'N/A')}")

    def log_message(self, format, *args):
        """Suppress default request logging — we have our own."""
        pass


def run_server(port: int = 8000):
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"Webhook server listening on port {port}")
    print(f"Configure Retell webhook URL: http://<your-ngrok-url>/call-events")
    print("Waiting for call events...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down webhook server.")
        server.server_close()

    # Print summary of all calls
    if call_results:
        print("\n" + "=" * 60)
        print("CALL RESULTS SUMMARY")
        print("=" * 60)
        for call_id, result in call_results.items():
            d = result.get("disposition")
            action = d["action"] if d else "none"
            print(f"  {call_id}: {action} ({result['duration_ms'] / 1000:.1f}s)")


if __name__ == "__main__":
    run_server()
