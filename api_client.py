import aiohttp
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from aiolimiter import AsyncLimiter
from datetime import datetime
from sqlalchemy import desc

from database import session_scope, Conversation, ConversationMessage, TranscriptSummary

logger = logging.getLogger(__name__)

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
                            response_text = await response.text()
                            logger.error(f"API request failed: {response.status}\nResponse: {response_text}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            else:
                                return None
                except Exception as e:
                    logger.error(f"Error making API request: {e}")
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
        logger.info(f"Starting scheduled sync at {datetime.now()}")
        conversations = await fetch_recent_conversations()

        with session_scope() as session:
            for conv in conversations:
                try:
                    existing_conv = session.query(Conversation).filter_by(conversation_id=conv['id']).first()
                    if existing_conv is None:
                        new_conv = Conversation(
                            conversation_id=conv['id'],
                            agent_id=AGENT_ID,
                            start_time=datetime.fromisoformat(conv['startedAt'].replace('Z', '+00:00')),
                            end_time=datetime.fromisoformat(conv['endedAt'].replace('Z', '+00:00')) if conv['endedAt'] else None,
                            summary=conv.get('summary', '')
                        )
                        session.add(new_conv)
                        logger.info(f"Added new conversation: {conv['id']}")

                        # Fetch and add conversation messages
                        messages = await fetch_conversation_transcript(conv['id'])
                        for msg in messages:
                            new_msg = ConversationMessage(
                                conversation_id=conv['id'],
                                role=msg['role'],
                                content=msg['content'],
                                timestamp=datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                            )
                            session.add(new_msg)
                        logger.info(f"Added {len(messages)} messages for conversation {conv['id']}")

                    else:
                        # Update existing conversation if needed
                        existing_conv.end_time = datetime.fromisoformat(conv['endedAt'].replace('Z', '+00:00')) if conv['endedAt'] else None
                        existing_conv.summary = conv.get('summary', '')
                        logger.info(f"Updated existing conversation: {conv['id']}")

                    # Add summary to TranscriptSummary
                    new_summary = TranscriptSummary(
                        content=conv.get('summary', ''),
                        created_at=datetime.utcnow()
                    )
                    session.add(new_summary)
                    logger.info(f"Added new transcript summary for conversation: {conv['id']}")

                except Exception as e:
                    logger.error(f"Error processing conversation {conv['id']}: {str(e)}")

        logger.info(f"Finished scheduled sync at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error during scheduled sync: {str(e)}")
        logger.exception("Full traceback:")

async def test_api_connection() -> bool:
    url = f"{PLAY_AI_API_URL}/agents/{AGENT_ID}/conversations"
    headers = {
        "Authorization": f"Bearer {PLAY_AI_API_KEY}",
        "X-USER-ID": PLAY_AI_USER_ID,
        "Accept": "application/json"
    }
    params = {"limit": 1}  # We only need one conversation to test the connection

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

async def run_sync():
    connection_success = await test_api_connection()
    if connection_success:
        await scheduled_sync()
    else:
        logger.error("API connection test failed. Aborting sync operation.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sync Play.ai data")
    parser.add_argument('--agent_id', help="The agent ID for Play.ai")
    parser.add_argument('--api_key', help="The API key for Play.ai")
    parser.add_argument('--user_id', help="The user ID for Play.ai")

    args = parser.parse_args()

    global AGENT_ID, PLAY_AI_API_KEY, PLAY_AI_USER_ID
    AGENT_ID = AGENT_ID or args.agent_id
    PLAY_AI_API_KEY = PLAY_AI_API_KEY or args.api_key
    PLAY_AI_USER_ID = PLAY_AI_USER_ID or args.user_id

    if not all([PLAY_AI_API_URL, PLAY_AI_API_KEY, PLAY_AI_USER_ID, AGENT_ID]):
        logger.error("Missing required credentials. Please provide them via environment variables or command-line arguments.")
        parser.print_help()
        return

    try:
        asyncio.run(run_sync())
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()