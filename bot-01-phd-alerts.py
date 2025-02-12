from UTILS.bot import Bot
from UTILS.extra import get_date_cycle
import os.path
from dotenv import load_dotenv
import discord
from discord.ext import tasks

# Load SECRET variables
load_dotenv(override=True)
GMAIL_TOKEN = os.getenv('GMAIL_TOKEN')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

# Get dates
lower_str, upper_str = get_date_cycle()

# Fetch messages from GMAIL
search_query=f"in:inbox is:unread after:{lower_str} before:{upper_str} PhD"
messages_data = Bot()._gmail(GMAIL_TOKEN, search_query)

# Summarize messages from GMAIL
# Do not modify the JSON scheme key 'condition'
# The key is used to determine "to_send" condition in Bot()._message()
# Make sure to change the condition for Return bool if .... 

sys_instruct="""
You are an AI which helps in summarizing content in 100 words.

If there any links, which redirects to PhD Admission website, or 
tells about the research lab, or tells about how to proceed ahead,
please include that as well.

Return bool if the content is of PhD/Post-Doc Advertisement/Recruitment.

Use this JSON Schema:
Content = {'condition': bool, 'summary': str}
Return: Content
"""
messages_summary = Bot()._llm(GEMINI_API_KEY, messages_data, sys_instruct)

# Filter messages which needs to be sent via Discord
to_send = Bot()._message(messages_data, messages_summary)

# Discord setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Index to track which message to send
message_index = 0  

@tasks.loop(seconds=1)
async def send_message():
    """Sends the next message in the list every 5 minutes."""
    global message_index
    channel = client.get_channel(int(DISCORD_CHANNEL_ID))
    
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

client.run(DISCORD_BOT_TOKEN)