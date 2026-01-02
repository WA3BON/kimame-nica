import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    """.env に保存した refresh_token を使って Gmail API 認証を復元"""
    creds = Credentials(
        token=None,  # アクセストークンは refresh_token で自動取得
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES
    )
    service = build("gmail", "v1", credentials=creds)
    return service

def send_mail_with_gmail(to_email, subject, body):
    """個人 Gmail にメール送信"""
    try:
        service = get_gmail_service()
        sender = os.environ["GMAIL_SENDER"]

        message = EmailMessage()
        message.set_content(body)
        message["To"] = to_email
        message["From"] = sender
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        service.users().messages().send(
            userId="me",
            body={"raw": encoded_message}
        ).execute()

        print(f"メール送信成功: {to_email}")

    except Exception as e:
        print("Gmail送信エラー:", e)
