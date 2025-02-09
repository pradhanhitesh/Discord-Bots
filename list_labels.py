import os
import json
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    """Lists the user's Gmail labels using a service account."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Check if the credentials file exists
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Service account file not found: {creds_path}")

    # Open and print the JSON file contents to ensure it's valid
    with open(creds_path, "r") as f:
        creds_data = json.load(f)  # Load the JSON content to ensure it's valid
        print(json.dumps(creds_data, indent=4))  # Pretty print the JSON content

    # Create credentials using the service account JSON file
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
