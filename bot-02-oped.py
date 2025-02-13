from UTILS.oped import Oped
from UTILS.extra import delete_data
from bs4 import BeautifulSoup
import requests
import os.path
from dotenv import load_dotenv
import discord
from discord.ext import tasks

# Load SECRET variables
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_OPED_ID")

# URL of the webpage to scrape
url = "https://www.thehindu.com/opinion/op-ed/"

# Send an HTTP request to get the HTML content
response = requests.get(url)

# Check if request was successful
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    ece_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.ece')]
    ece_links = list(set([x for x in ece_links if 'op-ed' in x]))

to_send_message = []
to_send_attch = []
for link in ece_links:
    # Send an HTTP request to get the HTML content
    response = requests.get(link)
    print(link)

    # Check if request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        page_data = Oped()._process_page(soup, GEMINI_API_KEY, output_path='DATA', output_md=True)
        message, pdf_path = Oped()._message(page_data, 
                                            template_path="template/article.html", output_path="DATA")
        to_send_message.append(message)
        to_send_attch.append(pdf_path)
    else:
        continue

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
    
    # TODO Fix "In content: Must be 2000 or fewer in length."
    if channel and message_index < len(to_send_message):
        file = discord.File(to_send_attch[message_index])
        await channel.send(to_send_message[message_index], file=file)
        message_index += 1  # Move to the next message
    
    # Stop the loop and close the bot if all messages are sent
    if message_index >= len(to_send_message):
        send_message.stop()
        await client.close()  # Gracefully terminate the bot

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    if to_send_message:  # Start only if there are messages
        send_message.start()
    else:
        await client.close()  # Close immediately if no messages exist

client.run(DISCORD_BOT_TOKEN)

# Remove files from DATA
delete_data()