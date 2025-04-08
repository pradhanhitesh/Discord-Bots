from UTILS.bot import OpedTH
from UTILS.extra import delete_data, save_historical, load_historical
from bs4 import BeautifulSoup
import requests
import os.path
from dotenv import load_dotenv
import discord
from discord.ext import tasks
import hashlib

# Load SECRET variables
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_ART_TH_ID")

# URL of the webpage to scrape
urls = ["https://www.thehindu.com/news/national/",
       "https://www.thehindu.com/business/",
       "https://www.thehindu.com/news/international/"]


for url in urls:
    try:
        # Send an HTTP request to get the HTML content
        response = requests.get(url)

        # Check if request was successful
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            ece_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.ece')]
            ece_links = list(set([x for x in ece_links if url in x]))

        # Load historical data
        historial_oped = load_historical("DATA/historical_art_th.json")

        # Start collecting data
        to_send_message = []
        to_send_attch = []
        to_save = []
        for link in ece_links:
            hashed_link = hashlib.sha256(link.encode()).hexdigest()
            if hashed_link not in historial_oped:
                print(f"Collecting data for link {link}")

                # Send an HTTP request to get the HTML content
                response = requests.get(link)

                # Check if request was successful
                if response.status_code == 200:
                    # Parse the HTML content
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_data = OpedTH()._process_page(soup, GEMINI_API_KEY, output_path='DATA', 
                                                    output_md=True, summarize=False)
                    message, pdf_path = OpedTH()._message(page_data, 
                                                        template_path="template/article.html", output_path="DATA", summary=False)
                    to_send_message.append(message)
                    to_send_attch.append(pdf_path)
                    to_save.append(hashlib.sha256(link.encode()).hexdigest())
                else:
                    continue
            else:
                print(f"Skipping link {link}")

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

        # Store the hashed links with time
        save_historical("DATA/historical_art_th.json", to_save)

        # Remove files from DATA
        delete_data()
    
    except Exception as e:
        print(f"COULD NOT RUN FOR URL {url} due to {e}")
        continue