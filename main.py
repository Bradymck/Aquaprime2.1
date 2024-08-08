import os
import logging
import asyncio
import signal
from discord_bot import run_discord_bot
from twitch_bot import run_twitch_bot
from database import init_db
from api_client import scheduled_sync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UnifiedBot')

# List of required Replit secrets
required_secrets = [
    'DISCORD_TOKEN', 
    'DISCORD_GUILD_ID', 
    'TWITCH_IRC_TOKEN', 
    'TWITCH_CLIENT_ID', 
    'TWITCH_CHANNEL', 
    'TWITCH_NICK'
]

# Check for missing Replit secrets
missing_secrets = [secret for secret in required_secrets if secret not in os.environ]
if missing_secrets:
    logger.error(f"Missing required Replit secrets: {', '.join(missing_secrets)}")
    raise SystemExit(f"Missing required Replit secrets: {', '.join(missing_secrets)}")

# Ensure correct values for verification (be cautious with sensitive data)
logger.info(f"Replit secrets set: {', '.join(required_secrets)}")

async def start_bots():
    # Initialize database
    init_db()

    # Start scheduled sync
    asyncio.create_task(scheduled_sync())

    tasks = [
        run_discord_bot(),
        run_twitch_bot()
    ]
    await asyncio.gather(*tasks)

def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    # Add any cleanup code here
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        loop.run_until_complete(start_bots())
    except Exception as e:
        logger.error(f"Error running bots: {e}")
    finally:
        loop.close()
        logger.info("Bot shutdown complete.")

# From your main file or wherever you initialize OpenAI
from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

# From the file where you make the API call
async def generate_response(prompt):
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I encountered an error."