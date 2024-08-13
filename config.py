import os
from shared_utils import logger

def check_secrets():
    required_secrets = [
        'DISCORD_TOKEN', 'DISCORD_GUILD_ID', 'TWITCH_IRC_TOKEN',
        'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK', 'OPENAI_API_KEY'
    ]
    missing_secrets = [secret for secret in required_secrets if secret not in os.environ]
    if missing_secrets:

