import os
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

def print_gmail_labels():
    """Fetch and print Gmail labels using Workload Identity Federation."""
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    try:
        creds = Credentials.from_authorized_user_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=SCOPES)
        
        print(creds)
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
