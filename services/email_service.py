import os
import re
from services.gmail_service import send_email

def send_financial_report(recipient_email: str, subject: str, report_content: str, pdf_bytes: bytes | None = None) -> tuple[bool, str]:
    """
    Constructs and sends an email using Gmail API.
    """
    recipient = recipient_email.strip()
    if not recipient or not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", recipient):
        return False, "Please enter a valid recipient email address."

    if not report_content or not report_content.strip():
        return False, "Report content is empty. Please generate a report first."

    # Delegate to the Gmail service
    return send_email(
        recipient=recipient,
        subject=subject,
        body=report_content,
        pdf_bytes=pdf_bytes
    )
