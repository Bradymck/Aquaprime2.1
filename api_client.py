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
from cachetools import TTLCache
import time

# Environment variables
PLAY_AI_API_URL = os.getenv('PLAY_AI_API_URL', 'https://api.play.ai/api/v1')
PLAY_AI_API_KEY = os.getenv('PLAY_AI_API_KEY')
PLAY_AI_USER_ID = os.getenv('PLAY_AI_USER_ID')
AGENT_ID = os.getenv('AGENT_ID')

# Rate limiter: 10 requests per second
rate_limiter = Limiter(10 / 1)

# Add these variables at the top of the file
TOKEN_EXPIRY = None
TOKEN_CACHE = TTLCache(maxsize=1, ttl=3600)  # Cache token for 1 hour

async def refresh_token():
    global TOKEN_EXPIRY
    # Implement token refresh logic here
    # Update TOKEN_EXPIRY with new expiry time
    TOKEN_CACHE['token'] = new_token
    TOKEN_EXPIRY = time.time() + 3600  # Set expiry to 1 hour from now

async def get_valid_token():
    if 'token' not in TOKEN_CACHE or time.time() > TOKEN_EXPIRY:
        await refresh_token()
    return TOKEN_CACHE['token']

async def make_api_request(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    async with rate_limiter:
        for attempt in range(max_retries):
            try:
                token = await get_valid_token()
                headers['Authorization'] = f"Bearer {token}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 401:  # Unauthorized, token might be expired
                            await refresh_token()
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
    # 🔍 Check if AGENT_ID is set
    if not AGENT_ID:
        logger.error("AGENT_ID is not set")
        return []
    
    # 🌐 Prepare the API request
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }
    params = {"limit": 50, "offset": 0}  # 🔢 Adjust limit as needed

    try:
        # 📡 Make the API request
        response = await make_api_request(url, headers, params)
        if response and 'conversations' in response:
            return response['conversations']
        return []
    except Exception as e:
        # ❗ Log any errors
        logger.error(f"Error fetching recent conversations: {e}")
        return []

async def fetch_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    # 🔍 Check if AGENT_ID is set
    if not AGENT_ID:
        logger.error("AGENT_ID is not set")
        return None
    
    # 🌐 Prepare the API request
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations/{conversation_id}"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }

    return await make_api_request(url, headers)

async def fetch_conversation_transcript(conversation_id: str) -> Optional[List[Dict[str, Any]]]:
    # 🔍 Check if AGENT_ID is set
    if not AGENT_ID:
        logger.error("AGENT_ID is not set")
        return []
    
    # 🌐 Prepare the API request
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations/{conversation_id}/transcript"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }

    try:
        # 📡 Make the API request
        response = await make_api_request(url, headers)
        if response and 'messages' in response:
            return response['messages']
        return []
    except Exception as e:
        # ❗ Log any errors
        logger.error(f"Error fetching conversation transcript for {conversation_id}: {e}")
        return []

async def scheduled_sync():
    while True:
        try:
            # Add your sync logic here
            await asyncio.sleep(300)  # Run every 5 minutes
        except asyncio.CancelledError:
            logger.info("Scheduled sync task was cancelled.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in scheduled_sync: {e}")