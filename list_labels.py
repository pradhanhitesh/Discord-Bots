import os
from google.auth.transport.requests import Request
from google.auth.credentials import AnonymousCredentials
from google.auth import impersonated_credentials
from googleapiclient.discovery import build
import requests

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    # The token should be set as an environment variable or obtained from GitHub actions
    id_token = os.getenv("GOOGLE_ID_TOKEN")

    if not id_token:
        raise ValueError("Google Identity Token not found")

    # Using the identity token to impersonate the service account
    creds = impersonated_credentials.Credentials.from_authorized_user_info(
        info={
            "token": id_token,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        target_principal="discord-bot@phd-alerts.iam.gserviceaccount.com",
        scopes=SCOPES,
    )

    # Using the creds to authenticate API requests
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    if not labels:
        print("No labels found.")
        return
    print("Labels:")
    for label in labels:
        print(label["name"])

if __name__ == "__main__":
    main()
