"""Email client with SMTP delivery and console fallback.

Attempts real SMTP if SMTP_HOST is configured; falls back to console
print + file log otherwise. Uses stdlib only (no new dependencies).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM

logger = logging.getLogger(__name__)


EMAIL_TEMPLATE_HTML = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; }}
.header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
.content {{ padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }}
.section {{ margin-bottom: 20px; }}
.section h3 {{ color: #2563eb; margin-bottom: 8px; font-size: 16px; }}
.med-list {{ background: #f9fafb; padding: 12px; border-radius: 4px; }}
.med-list li {{ margin-bottom: 4px; }}
.next-steps {{ background: #ecfdf5; padding: 12px; border-radius: 4px; border-left: 4px solid #10b981; }}
.footer {{ margin-top: 20px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
</style></head>
<body>
<div class="header">
  <h2>Care Follow-Up Summary</h2>
  <p>{facility_name} Care Coordination Team</p>
</div>
<div class="content">
  <p>Dear {patient_first_name},</p>
  <p>Thank you for speaking with us today regarding your recent visit to {facility_name}
     on {discharge_date}. Below is a summary of your care information.</p>

  <div class="section">
    <h3>Discharge Summary</h3>
    <p>{discharge_highlights}</p>
  </div>

  <div class="section">
    <h3>Your Medications</h3>
    <div class="med-list">
      <ul>{medications_html}</ul>
    </div>
    <p><small>Please contact your pharmacy or care team if you have questions about any medication.</small></p>
  </div>

  <div class="section">
    <h3>Next Steps</h3>
    <div class="next-steps">
      {next_steps_html}
    </div>
  </div>

  <div class="section">
    <h3>Your Care Team</h3>
    <p>Attending physician: {attending_physician}</p>
    <p>If you have questions or concerns, please contact {facility_name} care coordination.</p>
  </div>

  <div class="footer">
    <p>This email was sent by {facility_name}'s care coordination team as part of your
       post-discharge follow-up. This is not a substitute for medical advice. If you are
       experiencing a medical emergency, please call 911.</p>
  </div>
</div>
</body>
</html>
"""

EMAIL_TEMPLATE_TEXT = """\
Care Follow-Up Summary
{facility_name} Care Coordination Team

Dear {patient_first_name},

Thank you for speaking with us today regarding your recent visit to {facility_name} on {discharge_date}.

DISCHARGE SUMMARY
{discharge_highlights}

YOUR MEDICATIONS
{medications_text}

NEXT STEPS
{next_steps_text}

YOUR CARE TEAM
Attending physician: {attending_physician}
If you have questions, contact {facility_name} care coordination.

---
This email was sent by {facility_name}'s care coordination team. This is not a substitute
for medical advice. If you are experiencing a medical emergency, please call 911.
"""


class EmailClient:
    """Sends follow-up emails via SMTP or console fallback."""

    def __init__(self):
        self.smtp_configured = bool(SMTP_HOST)

    async def send(self, to: str, subject: str, body_html: str, body_text: str) -> dict:
        if self.smtp_configured:
            return self._send_smtp(to, subject, body_html, body_text)
        return self._send_console(to, subject, body_text)

    def _send_smtp(self, to: str, subject: str, body_html: str, body_text: str) -> dict:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent via SMTP to %s", to)
            return {"status": "sent", "method": "smtp"}
        except Exception as e:
            logger.error("SMTP send failed: %s — falling back to console", e)
            return self._send_console(to, subject, body_text)

    def _send_console(self, to: str, subject: str, body_text: str) -> dict:
        print("\n" + "=" * 60)
        print("EMAIL (console fallback — SMTP not configured)")
        print("=" * 60)
        print(f"  To:      {to}")
        print(f"  From:    {EMAIL_FROM}")
        print(f"  Subject: {subject}")
        print("-" * 60)
        print(body_text)
        print("=" * 60 + "\n")
        logger.info("Email printed to console (SMTP not configured)")
        return {"status": "sent", "method": "console"}


def compose_email(context: dict, disposition: dict | None) -> dict:
    """Compose email content from patient context and call disposition."""
    patient_name = context.get("patient_first_name", "Patient")
    facility = context.get("facility_name", "Your Healthcare Provider")
    discharge_date = context.get("discharge_date", "your recent visit")
    attending = context.get("attending_physician", "your care team")

    # Discharge highlights
    diagnosis = context.get("discharge_diagnosis", "")
    disposition_desc = context.get("discharge_disposition", "")
    highlights = f"Diagnosis: {diagnosis}" if diagnosis and diagnosis != "Unknown" else ""
    if disposition_desc and disposition_desc != "Unknown":
        highlights += f"\nDisposition: {disposition_desc}"
    if not highlights:
        highlights = "Please refer to your discharge paperwork for details."

    # Medications
    meds = context.get("active_medications", [])
    if meds:
        meds_html = "".join(f"<li>{m}</li>" for m in meds)
        meds_text = "\n".join(f"  - {m}" for m in meds)
    else:
        meds_html = "<li>No active medications documented</li>"
        meds_text = "  No active medications documented"

    # Next steps based on disposition
    action = disposition.get("action", "") if disposition else ""
    params = disposition.get("parameters", {}) if disposition else {}

    if action == "schedule_followup_call":
        days = params.get("days_from_now", 7)
        next_steps_html = f"<p>You're doing well! We'll check in again in about <strong>{days} days</strong>. If anything changes, contact your care team.</p>"
        next_steps_text = f"You're doing well! We'll check in again in about {days} days. If anything changes, contact your care team."
    elif action == "schedule_appointment":
        reason = params.get("reason", "follow-up care")
        urgency = params.get("urgency", "routine")
        next_steps_html = f"<p>A <strong>{urgency}</strong> follow-up appointment is being scheduled for: {reason}. Our team will contact you with appointment details.</p>"
        next_steps_text = f"A {urgency} follow-up appointment is being scheduled for: {reason}. Our team will contact you with appointment details."
    elif action == "escalate_to_coordinator":
        next_steps_html = "<p>A care coordinator will be reaching out to you shortly to discuss your care needs.</p>"
        next_steps_text = "A care coordinator will be reaching out to you shortly to discuss your care needs."
    else:
        next_steps_html = "<p>Continue following your discharge instructions. Contact your care team if you have any questions.</p>"
        next_steps_text = "Continue following your discharge instructions. Contact your care team if you have any questions."

    subject = f"Your Care Follow-Up from {facility}"

    body_html = EMAIL_TEMPLATE_HTML.format(
        facility_name=facility,
        patient_first_name=patient_name,
        discharge_date=discharge_date,
        discharge_highlights=highlights.replace("\n", "<br>"),
        medications_html=meds_html,
        next_steps_html=next_steps_html,
        attending_physician=attending,
    )

    body_text = EMAIL_TEMPLATE_TEXT.format(
        facility_name=facility,
        patient_first_name=patient_name,
        discharge_date=discharge_date,
        discharge_highlights=highlights,
        medications_text=meds_text,
        next_steps_text=next_steps_text,
        attending_physician=attending,
    )

    return {
        "subject": subject,
        "body_html": body_html,
        "body_text": body_text,
    }
