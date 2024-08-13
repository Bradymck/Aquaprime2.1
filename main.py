import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from shared_utils import logger, log_info
from api_client import scheduled_sync
from discord.ext import commands
from discord import Intents
import aiofiles
import signal
from twitch_bot import run_twitch_bot
from discord_bot import run_discord_bot, bot
from api_client import scheduled_sync
from database import init_db
from shared_utils import logger, log_info
# Load environment variables
load_dotenv()

# Set up Discord bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
            messages=[{
                "role": "system",
                "content": "You are a helpful assistant."
            }, {
                "role": "user",
                "content": prompt
            }])
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I encountered an error."

async def run_discord_bot():
    try:
        await bot.start(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

async def run_twitch_bot_wrapper():
    try:
        await run_twitch_bot()
    except Exception as e:
        logger.error(f"Error running Twitch bot: {e}")
    finally:
        # Add any cleanup code for Twitch bot if necessary
        pass

async def shutdown(signal, loop):
    log_info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    log_info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def signal_handler():
    log_info("Received shutdown signal. Closing bots...")
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.remove_signal_handler(sig)
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))

async def main():
    log_info("Aqua Prime Bot Starting")

    # Initialize the database
    await init_db()
    log_info("Database initialized")

    # Set up signal handling
    signal_handler()

    try:
        # Start the scheduled sync task
        sync_task = asyncio.create_task(scheduled_sync())

        # Run the Discord bot
        discord_task = asyncio.create_task(run_discord_bot())

        # Run the Twitch bot
        twitch_task = asyncio.create_task(run_twitch_bot_wrapper())

        # Wait for all tasks to complete
        await asyncio.gather(sync_task, discord_task, twitch_task)
    except asyncio.CancelledError:
        logger.info("Main task was cancelled.")
    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
    finally:
        # Ensure all tasks are completed before exiting
        await bot.close()
        for task in asyncio.all_tasks():
            task.cancel()
        await asyncio.gather(*asyncio.all_tasks(), return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())

# Add this function to log commands asynchronously
async def log_command(command):
    async with aiofiles.open('game_commands.log', mode='a') as f:
        await f.write(f"{command}\n")

async def init_discord_bot():
    await bot.add_cog(DiscordBot(bot))
    logger.info("Discord bot initialized")