import os
import json
from googleapiclient.discovery import build
from google.auth.identity_pool import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    """Lists the user's Gmail labels using a service account."""
    f = open(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    key = json.load(f)

    # Create credentials using the service account JSON file
    creds = Credentials.from_info(key)

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
