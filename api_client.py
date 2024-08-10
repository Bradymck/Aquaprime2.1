import aiohttp
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from aiolimiter import AsyncLimiter
from colorama import init, Fore, Back, Style
from shared_utils import print_header, log_info, log_error

# Initialize colorama
init(autoreset=True)

# Aqua Prime themed colors
COLORS = {
    'header': Fore.WHITE + Back.BLUE,
    'info': Fore.BLACK + Back.CYAN,
    'success': Fore.BLACK + Back.GREEN,
    'warning': Fore.BLACK + Back.YELLOW,
    'error': Fore.WHITE + Back.RED,
    'reset': Style.RESET_ALL
}

# AquaPrime Formatter
class AquaPrimeFormatter(logging.Formatter):
    def format(self, record):
        log_color = COLORS['info']
        if record.levelno >= logging.ERROR:
            log_color = COLORS['error']
        elif record.levelno >= logging.WARNING:
            log_color = COLORS['warning']

        log_message = super().format(record)

        if record.levelno >= logging.ERROR:
            return f"{COLORS['error']}{log_message:<80}{COLORS['reset']}"
        else:
            return f"{log_color}{log_message:<80}{COLORS['reset']}"

# Logger setup
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    AquaPrimeFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Environment variables
PLAY_AI_API_URL = os.getenv('PLAY_AI_API_URL', 'https://api.play.ai/api/v1')
PLAY_AI_API_KEY = os.getenv('PLAY_AI_API_KEY')
PLAY_AI_USER_ID = os.getenv('PLAY_AI_USER_ID')
AGENT_ID = os.getenv('AGENT_ID')

# Rate limiter: 10 requests per second
rate_limiter = AsyncLimiter(10, 1)


async def make_api_request(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    async with rate_limiter:
        async with aiohttp.ClientSession() as session:
            for attempt in range(max_retries):
                try:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 404:
                            logger.warning(f"Resource not found: {url}")
                            return None
                        else:
                            logger.error(f"API request failed: {response.status}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            else:
                                return None
                except Exception as e:
                    logger.error(f"Error making API request: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        return None


async def test_api_connection() -> bool:
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }
    params = {"limit": 1}  # Only need one conversation to test the connection

    logger.info(f"Testing API connection to: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Params: {params}")

    result = await make_api_request(url, headers, params)
    if result is not None:
        logger.info("API connection test successful")
        return True
    else:
        logger.error("API connection test failed")
        return False


async def fetch_recent_conversations() -> List[Dict[str, Any]]:
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }
    params = {"limit": 10}

    result = await make_api_request(url, headers, params)
    return result if result else []


# Add definition for update_agent_knowledge
async def update_agent_knowledge(agent_id: str, knowledge_data: Dict[str, Any]) -> bool:
    url = f"{PLAY_AI_API_URL}/agents/{agent_id}/knowledge"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=knowledge_data) as response:
            if response.status == 200:
                logger.info(f"Successfully updated agent knowledge for agent {agent_id}")
                return True
            else:
                logger.error(f"Failed to update agent knowledge for agent {agent_id}, status: {response.status}")
                return False


async def run_sync():
    while True:
        connection_success = await test_api_connection()
        if connection_success:
            await scheduled_sync()
        else:
            logger.error("API connection test failed. Retrying in 5 minutes.")
        await asyncio.sleep(300)  # Wait for 5 minutes before the next sync attempt


async def start_scheduled_sync():
    if not all([PLAY_AI_API_URL, PLAY_AI_API_KEY, PLAY_AI_USER_ID, AGENT_ID]):
        logger.error("Missing required credentials. Please provide them via environment variables.")
        return

    try:
        await run_sync()
    except Exception as e:
        logger.error(f"An unexpected error occurred in start_scheduled_sync: {e}")