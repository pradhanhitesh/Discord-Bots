from UTILS.mail import MIMEMessage
import os.path
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from google import genai
from google.genai import types
import discord
from discord.ext import tasks

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Read TOKEN
secret_json = os.getenv('GMAIL_TOKEN')
creds = Credentials.from_authorized_user_info(json.loads(secret_json), SCOPES)

# Get messages
service = build("gmail", "v1", credentials=creds)
results = service.users().messages().list(userId='me', q="in:inbox is:unread after:2025/2/8 before:2025/2/9").execute()
messages = results.get('messages',[]);

# Extract content from messages
messages_data = {}
for k, message in enumerate(messages):
    msg = service.users().messages().get(userId='me', id=message['id']).execute()
    try:
        content = MIMEMessage()._extract_content(message=msg)
        meta = MIMEMessage()._collect_metadata(message=msg)
        messages_data[message['id']] = {"metadata": meta, "message": content}
    except Exception as e:
        print(f"{message['id']} due to {e}")
        continue

# Summarize message content
sys_instruct="""You are an AI which helps in summarizing content in 100 words and return bool if the content is of PhD/Post-Doc Advertisement/Recruitment.
Use this JSON Schema:

Content = {'ad': bool, 'summary': str}
Return: Content"""
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

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
    print(f"{message}: {response_json}")

# Discord setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# List of messages to send
to_send = []
for message in message_summary:
    content = [f"# Message ID: {message}\n"]
    if message_summary[message]['ad']:
        from_field = messages_data[message]['metadata']['From']
        subject = messages_data[message]['metadata']['Subject']
        summary = message_summary[message]['summary']

        content.append(f"### Message from {from_field}\n")
        content.append(f"##### **Subject:** {subject}\n")
        content.append(f"**Summary:** {summary}")
        to_send.append("".join(content))

# Index to track which message to send
message_index = 0  

@tasks.loop(seconds=300)  # Runs every 5 minutes
async def send_message():
    """Sends the next message in the list every 5 minutes."""
    global message_index
    channel = client.get_channel(int(os.getenv('DISCORD_CHANNEL_ID')))
    
    if channel and message_index < len(to_send):
        await channel.send(to_send[message_index])
        message_index += 1  # Move to the next message
    
    # Stop the loop and close the bot if all messages are sent
    if message_index >= len(to_send):
        send_message.stop()
        await client.close()  # Gracefully terminate the bot

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    if to_send:  # Start only if there are messages
        send_message.start()
    else:
        await client.close()  # Close immediately if no messages exist

client.run(os.getenv('DISCORD_BOT_TOKEN'))