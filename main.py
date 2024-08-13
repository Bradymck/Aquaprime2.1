import os
from dotenv import load_dotenv
import logging
import asyncio
import random
from datetime import datetime
from colorama import init, Fore, Style
from openai import AsyncOpenAI
from shared_utils import print_header, log_info
from api_client import scheduled_sync
from discord.ext import commands
from discord import Intents
import aiofiles
import signal
from twitch_bot import run_twitch_bot  # Add this import

# Initialize colorama
init(autoreset=True)

# Aqua Prime themed emojis and symbols
AQUA_EMOJIS = [
    "🌊", "💧", "🐠", "🐳", "🦈", "🐙", "🦀", "🐚", "🏊‍♂️", "🏄‍♂️", "🤿", "🚤"
]
# Load environment variables from .env file
load_dotenv()

class AquaPrimeFormatter(logging.Formatter):

    def format(self, record):
        emoji = random.choice(AQUA_EMOJIS)
        log_message = super().format(record)
        return f"{emoji} {log_message}"


# Set up logging
logger = logging.getLogger('UnifiedBot')
handler = logging.StreamHandler()
handler.setFormatter(
    AquaPrimeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                       datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# List of required Replit secrets
required_secrets = [
    'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN',
    'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY'
]

# Check for missing Replit secrets
missing_secrets = [
    secret for secret in required_secrets if secret not in os.environ
]
if missing_secrets:
    logger.error(
        f"Missing required Replit secrets: {', '.join(missing_secrets)}")
    raise SystemExit(
        f"Missing required Replit secrets: {', '.join(missing_secrets)}")

logger.info(f"Replit secrets set: {', '.join(required_secrets)}")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])


async def generate_response(prompt):
    try:
        logger.info(f"Sending prompt to OpenAI: {prompt[:50]}..."
                    )  # Log first 50 chars of prompt
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant."
            }, {
                "role": "user",
                "content": prompt
            }])
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I encountered an error."


async def run_discord_bot():
    from discord_bot import run_discord_bot as discord_run
    await discord_run()


async def main():
    print_header("Aqua Prime Bot Starting")

    from database import init_db

    # Initialize the database
    await init_db()
    log_info("Database initialized")

    # Start the scheduled sync task
    sync_task = asyncio.create_task(scheduled_sync())

    # Run the Discord bot
    discord_task = asyncio.create_task(run_discord_bot())

    # Run the Twitch bot
    twitch_task = asyncio.create_task(run_twitch_bot())

    # Wait for all tasks to complete
    await asyncio.gather(sync_task, discord_task, twitch_task)


def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    for task in asyncio.all_tasks():
        task.cancel()
    asyncio.get_event_loop().stop()


if __name__ == "__main__":
    logger.info("Aqua Prime Bot Initializing")
    loop = asyncio.get_event_loop()

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running bots: {e}")
    finally:
        logger.info(
            f"{Fore.YELLOW}{Style.BRIGHT}Aqua Prime Bot Shutdown Complete{Style.RESET_ALL}"
        )

# Make sure this is after main to avoid the circular import issue
intents = Intents.default()  # Define intents
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix="!", intents=intents)  # Pass intents to bot


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    await setup()  # Load the commands cog when the bot is ready

async def setup():
    from discord_bot import DiscordBot
    await bot.add_cog(DiscordBot(bot))
    await bot.tree.sync()  # Sync the application commands

# Add this function to log commands asynchronously
async def log_command(command):
    async with aiofiles.open('game_commands.log', mode='a') as f:
        await f.write(f"{command}\n")