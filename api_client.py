import logging
import aiohttp
import asyncio
import os
from sqlalchemy import select
from database import session_scope, Conversation, ConversationMessage
from typing import List, Dict, Any, Optional
from asynciolimiter import Limiter
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# Initialize logging
logger = logging.getLogger('UnifiedBot')
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Environment variables
PLAY_AI_API_URL = os.getenv('PLAY_AI_API_URL', 'https://api.play.ai/api/v1')
PLAY_AI_API_KEY = os.getenv('PLAY_AI_API_KEY')
PLAY_AI_USER_ID = os.getenv('PLAY_AI_USER_ID')
AGENT_ID = os.getenv('AGENT_ID')

# Rate limiter: 10 requests per second
rate_limiter = Limiter(10 / 1)

async def make_api_request(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    async with rate_limiter:
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
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
                        existing_conv = await session.execute(select(Conversation).filter_by(conversation_id=conv['id']))
                        existing_conv = existing_conv.scalar_one_or_none()
                        if existing_conv is None:
                            new_conv = Conversation(
                                conversation_id=conv['id'],
                                agent_id=AGENT_ID,
                                start_time=datetime.fromisoformat(conv['startedAt'].replace('Z', '+00:00')),
                                end_time=datetime.fromisoformat(conv['endedAt'].replace('Z', '+00:00')) if conv['endedAt'] else None,
                                summary=conv.get('summary', '')
                            )
                            session.add(new_conv)
                            await session.flush()
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

                await session.commit()

            logger.info(f"Sync complete. New conversations: {new_count}, Updated: {update_count}, Messages: {message_count}")
            await asyncio.sleep(300)

    except asyncio.CancelledError:
        logger.info("Scheduled sync task was cancelled.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in scheduled_sync: {e}")