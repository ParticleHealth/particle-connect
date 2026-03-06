#!/usr/bin/env python3
"""Signal Webhook Receiver: Listen for Particle Health transit alerts.

This script starts a local HTTP server that receives CloudEvents webhook
payloads from Particle Health's Signal (transit alerts) service.

Prerequisites:
    1. Register a webhook URL with Particle Health pointing to this server.
    2. Use ngrok or a similar tunnel to expose your local server:
           ngrok http 8080
       Then register the resulting https URL (e.g. https://abc123.ngrok.io/webhook)
       as your webhook endpoint in Particle Health.

Usage:
    python workflows/signal_webhook_receiver.py

    # Or with a custom port:
    WEBHOOK_PORT=9090 python workflows/signal_webhook_receiver.py

Environment variables:
    - WEBHOOK_PORT: Port to listen on (default: 8080)
"""

import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


class WebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhook POST requests."""

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            print(f"[{_timestamp()}] WARNING: Received invalid JSON")
            self.send_response(400)
            self.end_headers()
            return

        _print_event(payload)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def log_message(self, format, *args):
        """Suppress default request logging to keep output clean."""
        pass


def _timestamp() -> str:
    """Return current UTC timestamp as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _print_event(payload: dict) -> None:
    """Pretty-print a CloudEvents webhook payload."""
    timestamp = _timestamp()
    event_type = payload.get("type", "unknown")
    subject = payload.get("subject", "unknown")
    event_id = payload.get("id", "unknown")
    event_time = payload.get("time", "unknown")
    data = payload.get("data", {})

    # Identify alert type from the data payload
    alert_type = data.get("event_type", subject)
    patient_id = data.get("particle_patient_id", "unknown")

    print(f"\n{'=' * 60}")
    print(f"  Webhook received at {timestamp}")
    print(f"{'=' * 60}")
    print(f"  Alert Type : {alert_type}")
    print(f"  Subject    : {subject}")
    print(f"  Event Type : {event_type}")
    print(f"  Event ID   : {event_id}")
    print(f"  Event Time : {event_time}")
    print(f"  Patient ID : {patient_id}")

    if data:
        print(f"\n  Data:")
        for key, value in data.items():
            print(f"    {key}: {value}")

    print(f"{'=' * 60}\n")


def main() -> None:
    """Start the webhook receiver server."""
    port = int(os.environ.get("WEBHOOK_PORT", "8080"))

    print(f"=== Signal Webhook Receiver ===\n")
    print(f"Listening on http://localhost:{port}/webhook")
    print(f"\nTo expose publicly, run:")
    print(f"  ngrok http {port}")
    print(f"\nThen register the ngrok HTTPS URL as your webhook endpoint.\n")
    print("Waiting for webhooks...\n")

    server = HTTPServer(("", port), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
