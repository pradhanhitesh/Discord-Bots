import os
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def print_gmail_labels():
    """Fetch and print Gmail labels using Workload Identity Federation."""
    try:
        creds, _ = default()  # Automatically fetch credentials from GitHub Actions
        service = build("gmail", "v1", credentials=creds)

        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return

        print("Labels:")
        for label in labels:
            print(label["name"])

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    print_gmail_labels()
