import os
import logging
import asyncio
import signal
import random
from datetime import datetime
from colorama import init, Fore, Style
from discord_bot import run_discord_bot
from twitch_bot import run_twitch_bot
from database import init_db
from api_client import scheduled_sync
from openai import AsyncOpenAI

# Initialize colorama
init(autoreset=True)

# Aqua Prime themed emojis and symbols
AQUA_EMOJIS = ["🌊", "💧", "🐠", "🐳", "🦈", "🐙", "🦀", "🐚", "🏊‍♂️", "🏄‍♂️", "🤿", "🚤"]

class AquaPrimeFormatter(logging.Formatter):
    def format(self, record):
        aqua_colors = [Fore.CYAN, Fore.BLUE, Fore.GREEN]
        color = random.choice(aqua_colors)
        emoji = random.choice(AQUA_EMOJIS)

        log_message = super().format(record)
        return f"{color}{Style.BRIGHT}{emoji} {log_message}{Style.RESET_ALL}"

# Set up logging
logger = logging.getLogger('UnifiedBot')
handler = logging.StreamHandler()
handler.setFormatter(AquaPrimeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# List of required Replit secrets
required_secrets = [
    'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN', 'TWITCH_CLIENT_ID',
    'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY'
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
        logger.info(f"Sending prompt to OpenAI: {prompt[:50]}...")  # Log first 50 chars of prompt
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I encountered an error."

async def main():
    print_header("Aqua Prime Bot Starting")

    # Import the run functions here to avoid circular imports
    from discord_bot import run_discord_bot
    from twitch_bot import run_twitch_bot  # If you have a Twitch bot

    await run_discord_bot()
    # await run_twitch_bot()  # Uncomment if you have a Twitch bot

def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'🌊' * 40}{Style.RESET_ALL}")
    logger.info(f"{Fore.YELLOW}{Style.BRIGHT}Aqua Prime Bot Initializing{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'🌊' * 40}{Style.RESET_ALL}\n")

    loop = asyncio.get_event_loop()

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Error running bots: {e}")
    finally:
        loop.close()
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'🌊' * 40}{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}{Style.BRIGHT}Aqua Prime Bot Shutdown Complete{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'🌊' * 40}{Style.RESET_ALL}\n")