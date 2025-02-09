import os
import json
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    """Lists the user's Gmail labels using a service account."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Debug: Print if the file exists
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Service account file not found: {creds_path}")

    # Debug: Print file contents to check if it's valid JSON (remove this in production)
    with open(creds_path, "r") as f:
        try:
            json.load(f)  # Check if the file is valid JSON
        except json.JSONDecodeError:
            raise ValueError("Service account file is not valid JSON.")

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)

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