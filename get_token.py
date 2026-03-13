from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def main():

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        SCOPES
    )

    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent"
    )

    print("\n=== 認証成功 ===")
    print("access_token:", creds.token)
    print("refresh_token:", creds.refresh_token)

    # Gmail API 接続
    service = build("gmail", "v1", credentials=creds)

    print("\nGmail API 接続成功")

if __name__ == "__main__":
    main()