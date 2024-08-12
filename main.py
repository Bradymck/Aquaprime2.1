# main.py

import os
import logging
import asyncio
import signal
import random
from datetime import datetime
from colorama import init, Fore, Style
from database import init_db
init_db()  # Ensure the database is initialized
from api_client import scheduled_sync
from openai import OpenAI  # Changed from AsyncOpenAI to OpenAI
from shared_utils import print_header, log_info, log_error, log_warning, generate_response
from game_state_manager import GameStateManager  # Ensure this import is present

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

# List of required environment variables
required_env_vars = [
    'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN', 'TWITCH_CLIENT_ID',
    'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY', 'PLAY_AI_API_KEY',
    'PLAY_AI_USER_ID', 'AGENT_ID', 'PLAY_AI_API_URL'
]

# Check for missing environment variables
missing_env_vars = [var for var in required_env_vars if var not in os.environ]
if missing_env_vars:
    log_error(f"Missing required environment variables: {', '.join(missing_env_vars)}")
    raise SystemExit(f"Missing required environment variables: {', '.join(missing_env_vars)}")

log_info(f"All required environment variables are set")

# Check for PyNaCl
try:
    import nacl
except ImportError:
    log_warning("PyNaCl is not installed, voice features will not be available. To install, run: pip install pynacl")

# Initialize OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Initialize GameStateManager
repo_path = "./AquaPrimeLORE"
file_path = "./AquaPrimeLORE/game_state.json"
game_state_manager = GameStateManager(repo_path, file_path)

async def main():
    print_header("Aqua Prime Bot Starting")

    # Initialize database
    init_db()
    log_info("Database initialized")

    # Start the scheduled sync task
    sync_task = asyncio.create_task(scheduled_sync())
    log_info("Scheduled sync task started")

    # Start the Discord bot
    discord_task = asyncio.create_task(run_discord_bot())
    log_info("Discord bot started")

    # Start the Twitch bot
    twitch_task = asyncio.create_task(run_twitch_bot())
    log_info("Twitch bot started")

    # Wait for both bots to complete (which should be never, unless there's an error)
    await asyncio.gather(discord_task, twitch_task, sync_task)

def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    for task in asyncio.all_tasks():
        task.cancel()
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