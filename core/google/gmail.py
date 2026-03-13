import base64
import os
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=credentials)


def send_mail_with_gmail(*, to_email, subject, body, sender_name):
    """
    sender_name: Owner.name from the database
    """
    service = get_gmail_service()
    sender_email = os.environ["GMAIL_SENDER"]

    message = EmailMessage()
    message.set_content(body)

    message["To"] = to_email
    message["From"] = f"{sender_name} <{sender_email}>"
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": encoded_message},
    ).execute()

    print(f"Email sent successfully → {to_email}")
