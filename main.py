import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from shared_utils import logger, log_info
from api_client import scheduled_sync
from discord.ext import commands
from discord import Intents
import aiofiles
import signal
from twitch_bot import run_twitch_bot

# Load environment variables
load_dotenv()

# Set up Discord bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# List of required Replit secrets
required_secrets = [
    'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN',
    'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY'
]

# Check for missing Replit secrets
missing_secrets = [secret for secret in required_secrets if secret not in os.environ]
if missing_secrets:
    logger.error(f"Missing required Replit secrets: {', '.join(missing_secrets)}")
    raise SystemExit(f"Missing required Replit secrets: {', '.join(missing_secrets)}")

logger.info(f"Replit secrets set: {', '.join(required_secrets)}")

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

async def generate_response(prompt):
    try:
        logger.info(f"Sending prompt to OpenAI: {prompt[:50]}...")
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

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running bots: {e}")
    finally:
        logger.info("Aqua Prime Bot Shutdown Complete")

# Add this function to log commands asynchronously
async def log_command(command):
    async with aiofiles.open('game_commands.log', mode='a') as f:
        await f.write(f"{command}\n")