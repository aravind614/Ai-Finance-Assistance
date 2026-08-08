from services.email_service import send_financial_report

def send_email_report(recipient_email: str, subject: str = "AI Investment Research Report", report_content: str = "", pdf_bytes: bytes = None) -> str:
    """
    Simpler email agent wrapper.
    """
    success, message = send_financial_report(recipient_email, subject, report_content, pdf_bytes)
    return message
