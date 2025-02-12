from UTILS.mail import MIMEMessage
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()

class Bot():
    def __init__(self):
        pass

    def _gmail(self, GMAIL_TOKEN: dict, search_query: str):
        # Sanity checks
        if not isinstance(GMAIL_TOKEN, str):
            raise ValueError(f"GMAIL_TOKEN expects a dictionary (parsed JSON). Instead got {type(GMAIL_TOKEN).__name__}")

        # If modifying these scopes, delete the file token.json
        # And generate token.json again using generate_tokens.py
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
        creds = Credentials.from_authorized_user_info(json.loads(GMAIL_TOKEN), SCOPES)

        # Get messages
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId='me', q=search_query).execute()
        messages = results.get('messages',[]);

        # Extract content from messages
        messages_data = {}
        for _, message in enumerate(messages):
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            try:
                content = MIMEMessage()._extract_content(message=msg)
                meta = MIMEMessage()._collect_metadata(message=msg)
                messages_data[message['id']] = {"metadata": meta, "message": content}
            except Exception as e:
                print(f"Unable to retireve message ID: {message['id']} due to error: {e}")
                continue

        return messages_data

    def _llm(self, GEMINI_API_KEY: str, messages_data: dict, sys_instruct: str):
        # Setup client
        client = genai.Client(api_key=GEMINI_API_KEY)

        message_summary = {}
        for message in messages_data:
            content = messages_data[message]['message']
            response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                max_output_tokens=500,
                temperature=0.1),
                contents=[content],)
            
            if "```json" in response.text:
                # Clean the response by removing the code block markers
                response_content_cleaned = response.text.replace("```json", "").replace("```", "").strip()
                response_json = json.loads(response_content_cleaned)
            else:
                # Parse the response content back to a Python dictionary
                response_json = json.loads(response.text)

            message_summary[message] = response_json

        return message_summary

    def _message(self, messages_data: dict, message_summary: dict):
        # List of messages to send
        to_send = []
        for message in message_summary:
            # content = [f"# Message ID: {message}\n"]
            if message_summary[message]['condition']:
                from_field = messages_data[message]['metadata']['From']
                subject = messages_data[message]['metadata']['Subject']
                date = messages_data[message]['metadata']['Date']
                summary = message_summary[message]['summary']

                content = []
                content.append(f"### 📝 **Subject:** {subject}\n")
                content.append(f"### **Date:** {date}\n")
                content.append(f"### Message from {from_field}\n")
                content.append(f"**Summary:** {summary}")
                to_send.append("".join(content))

        return to_send