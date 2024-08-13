import aiohttp
import asyncio
import os
from contextlib import asynccontextmanager
from sqlalchemy import select
from database import session_scope, Conversation, ConversationMessage
from typing import List, Dict, Any, Optional
from asynciolimiter import Limiter
from datetime import datetime
from shared_utils import logger

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
            except Exception as e:
                logger.error(f"Error making API request: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        return None

async def fetch_recent_conversations() -> List[Dict[str, Any]]:
    if not AGENT_ID:
        logger.error("AGENT_ID is not set")
        return []
    
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }
    params = {"limit": 50, "offset": 0}  # Adjust limit as needed

    try:
        response = await make_api_request(url, headers, params)
        if response and 'conversations' in response:
            return response['conversations']
        return []
    except Exception as e:
        logger.error(f"Error fetching recent conversations: {e}")
        return []

async def fetch_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    if not AGENT_ID:
        logger.error("AGENT_ID is not set")
        return None
    
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations/{conversation_id}"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }

    return await make_api_request(url, headers)

async def fetch_conversation_transcript(conversation_id: str) -> Optional[List[Dict[str, Any]]]:
    if not AGENT_ID:
        logger.error("AGENT_ID is not set")
        return []
    
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations/{conversation_id}/transcript"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }

    try:
        response = await make_api_request(url, headers)
        if response and 'messages' in response:
            return response['messages']
        return []
    except Exception as e:
        logger.error(f"Error fetching conversation transcript for {conversation_id}: {e}")
        return []