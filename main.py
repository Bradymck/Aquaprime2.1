import os
import logging
import asyncio
import signal
import random
from colorama import init, Fore, Style
from discord_bot import run_discord_bot

# Initialize colorama
init(autoreset=True)

class AquaPrimeFormatter(logging.Formatter):
    def format(self, record):
        aqua_colors = [Fore.CYAN, Fore.BLUE, Fore.GREEN]
        color = random.choice(aqua_colors)
        emoji = random.choice(["🌊", "💧", "🐠", "🐳", "🦈", "🐙", "🦀", "🐚", "🏊‍♂️", "🏄‍♂️", "🤿", "🚤"])

        log_message = super().format(record)
        return f"{color}{Style.BRIGHT}{emoji} {log_message}{Style.RESET_ALL}"

logger = logging.getLogger('UnifiedBot')
handler = logging.StreamHandler()
handler.setFormatter(AquaPrimeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

required_secrets = [
    'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN', 'TWITCH_CLIENT_ID',
    'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY'
]

missing_secrets = [secret for secret in required_secrets if secret not in os.environ]
if missing_secrets:
    logger.error(f"Missing required secrets: {', '.join(missing_secrets)}")
    raise SystemExit(f"Missing required secrets: {', '.join(missing_secrets)}")

logger.info(f"Secrets set: {', '.join(required_secrets)}")

async def main():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'🌊' * 40}{Style.RESET_ALL}")
    logger.info(f"{Fore.YELLOW}{Style.BRIGHT}Aqua Prime Bot Initializing{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'🌊' * 40}{Style.RESET_ALL}\n")

    await run_discord_bot()

def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

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