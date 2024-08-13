import os
from openai import AsyncOpenAI
from shared_utils import logger

def check_secrets():
    required_secrets = [
        'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN',
        'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY',
        'PLAY_AI_API_KEY', 'PLAY_AI_USER_ID', 'AGENT_ID', 'PLAY_AI_API_URL'
    ]
    missing_secrets = [secret for secret in required_secrets if secret not in os.environ]
    if missing_secrets:
        logger.error(f"Missing required secrets: {', '.join(missing_secrets)}")
        raise SystemExit(f"Missing required secrets: {', '.join(missing_secrets)}")
    logger.info(f"All required secrets are set")

def initialize_openai_client():
    return AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

PLAY_AI_API_URL = os.getenv('PLAY_AI_API_URL', 'https://api.play.ai/api/v1')
PLAY_AI_API_KEY = os.environ['PLAY_AI_API_KEY']
PLAY_AI_USER_ID = os.environ['PLAY_AI_USER_ID']
AGENT_ID = os.environ['AGENT_ID']