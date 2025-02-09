import os.path
import base64
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
secret_json = os.environ.get('MY_SECRET_JSON')

def main():
    decoded_json = base64.b64decode(secret_json).decode("utf-8")
    data = json.loads(decoded_json)
    print(data)
    creds = Credentials.from_authorized_user_info(data, SCOPES)

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
        print("Labels:")

        for label in labels:
            print(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()