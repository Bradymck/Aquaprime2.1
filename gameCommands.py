import os
import asyncio
import signal
from database import init_db
from api_client import scheduled_sync
from openai import AsyncOpenAI
from shared_utils import logger, log_info
import aiofiles

# List of required Replit secrets
required_secrets = [
    'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN',
    'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY'
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
        logger.info(f"Sending prompt to OpenAI: {prompt[:50]}...")
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "An error occurred while generating the response."