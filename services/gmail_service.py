import os
import base64
from typing import Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service() -> Any:
    """
    Authenticate and return the Gmail API service.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("Google OAuth client configuration file 'credentials.json' is missing.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            
    return build("gmail", "v1", credentials=creds)

def send_email(recipient: str, subject: str, body: str, pdf_bytes: bytes | None = None) -> tuple[bool, str]:
    """
    Sends an email using the Gmail API.
    """
    try:
        service: Any = get_gmail_service()
        
        message = MIMEMultipart()
        message["to"] = recipient
        message["subject"] = subject
        
        # Attach the body text
        message.attach(MIMEText(body, "plain"))
        
        # Attach PDF bytes if present
        if pdf_bytes:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment; filename=\"Investment_Report.pdf\"",
            )
            message.attach(part)
            
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_payload = {"raw": raw_message}
        
        service.users().messages().send(userId="me", body=send_payload).execute()
        return True, "✅ Email sent successfully"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"
