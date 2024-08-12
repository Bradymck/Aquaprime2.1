import aiohttp
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from asynciolimiter import Limiter  # Corrected import statement
from datetime import datetime
from colorama import init, Fore, Back, Style
import tracemalloc
tracemalloc.start()
import aiofiles

from database import session_scope, Conversation, ConversationMessage

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

class AquaPrimeFormatter(logging.Formatter):
    def format(self, record):
        log_color = COLORS['info']
        if record.levelno >= logging.ERROR:
            log_color = COLORS['error']
        elif record.levelno >= logging.WARNING:
            log_color = COLORS['warning']

        log_message = super().format(record)

        # Highlight the entire line for errors
        if record.levelno >= logging.ERROR:
            return f"{COLORS['error']}{log_message:<80}{COLORS['reset']}"
        else:
            return f"{log_color}{log_message:<80}{COLORS['reset']}"

logger = logging.getLogger('UnifiedBot')
handler = logging.StreamHandler()
handler.setFormatter(AquaPrimeFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Environment variables
PLAY_AI_API_URL = os.getenv('PLAY_AI_API_URL', 'https://api.play.ai/api/v1')
PLAY_AI_API_KEY = os.getenv('PLAY_AI_API_KEY')
PLAY_AI_USER_ID = os.getenv('PLAY_AI_USER_ID')
AGENT_ID = os.getenv('AGENT_ID')

# Rate limiter: 10 requests per second
rate_limiter = Limiter(10 / 1)  # Corrected import statement

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

async def fetch_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations/{conversation_id}"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }

    return await make_api_request(url, headers)

async def fetch_conversation_transcript(conversation_id: str) -> Optional[List[Dict[str, Any]]]:
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations/{conversation_id}/transcript"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }

    return await make_api_request(url, headers)

async def scheduled_sync():
    try:
        while True:
            conversations = await fetch_recent_conversations()
            if not conversations:
                logger.info("No new conversations to sync.")
                await asyncio.sleep(300)
                continue

            new_count = 0
            update_count = 0
            message_count = 0

            async with session_scope() as session:
                for conv in conversations:
                    try:
                        existing_conv = await session.execute(select(Conversation).filter_by(conversation_id=conv['id'])).scalar_one_or_none()
                        if existing_conv is None:
                            new_conv = Conversation(
                                conversation_id=conv['id'],
                                agent_id=AGENT_ID,
                                start_time=datetime.fromisoformat(conv['startedAt'].replace('Z', '+00:00')),
                                end_time=datetime.fromisoformat(conv['endedAt'].replace('Z', '+00:00')) if conv['endedAt'] else None,
                                summary=conv.get('summary', '')
                            )
                            session.add(new_conv)
                            new_count += 1

                            messages = await fetch_conversation_transcript(conv['id'])
                            for msg in messages:
                                if 'content' in msg:
                                    new_msg = ConversationMessage(
                                        conversation_id=conv['id'],
                                        role=msg['role'],
                                        content=msg['content'],
                                        timestamp=datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                                    )
                                    session.add(new_msg)
                                else:
                                    logger.error(f"Message does not contain 'content': {msg}")
                            message_count += len(messages)
                        else:
                            update_count += 1
                    except Exception as e:
                        logger.error(f"Sync error: {str(e)}")

            logger.info(f"Sync complete. New conversations: {new_count}, Updated: {update_count}, Messages: {message_count}")
            await asyncio.sleep(300)

    except asyncio.CancelledError:
        logger.info("Scheduled sync task was cancelled.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in scheduled_sync: {e}")

async def run_sync():
    while True:
        try:
            connection_success = await test_api_connection()
            if connection_success:
                await scheduled_sync()
            else:
                logger.error("API connection test failed. Retrying in 5 minutes.")
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"An error occurred in run_sync: {e}")
            await asyncio.sleep(300)

async def start_scheduled_sync():
    if not all([PLAY_AI_API_URL, PLAY_AI_API_KEY, PLAY_AI_USER_ID, AGENT_ID]):
        logger.error("Missing required credentials. Please provide them via environment variables.")
        return

    try:
        await run_sync()
    except Exception as e:
        logger.error(f"An unexpected error occurred in start_scheduled_sync: {e}")

if __name__ == "__main__":
    asyncio.run(start_scheduled_sync())