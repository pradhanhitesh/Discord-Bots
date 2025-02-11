""""
============================================================================
Adapted from: https://developers.google.com/gmail/api/quickstart/python 

The following script is used to generate tokens for GMail API authentication once
OAuth2.0 credentials file has been generated and stored in the current working
directory under name credentials.json

Once, credentials.json file is generated and stored in the current working 
directory, run the following script to authenticate once and then generate
token.json file. The newly generated token.json file will be used in future 
for authentication anytime GMail Services are used. No need for authentication
again. 

This token.json file is used as repository secret in GitHub Actions. Be sure to 
keep it safe in the Settings > Secrets and Variables > Actions > Repository Secrets 

Further reading, https://developers.google.com/gmail/api/auth/web-server
=============================================================================
"""

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      if not os.path.exists("credentials.json"):
        raise AttributeError("Could not find credentials.json file")
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

if __name__ == "__main__":
  main()