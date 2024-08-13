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
from database import init_db
from shared_utils import logger, log_info
from game_state_manager import GameStateManager
from plugin_manager import PluginManager
from config import check_secrets, initialize_openai_client  # Add this line

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
        await bot.add_cog(DiscordBot(bot))
        await bot.tree.sync()  # Ensure the commands are synced
        await bot.start(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

async def shutdown(signal, loop):
    log_info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    log_info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def run_twitch_bot_wrapper():
    try:
        await run_twitch_bot()
    except Exception as e:
        logger.error(f"Error running Twitch bot: {e}")
    finally:
        # Add any cleanup code for Twitch bot if necessary
        pass

async def main():
    log_info("Aqua Prime Bot Starting")
    check_secrets()
    openai_client = initialize_openai_client()

    try:
        await init_db()
        log_info("Database initialized")

        game_state_manager = GameStateManager("./AquaPrimeLORE", "./AquaPrimeLORE/game_state.json")
        sync_task = asyncio.create_task(game_state_manager.scheduled_sync())
        discord_task = asyncio.create_task(run_discord_bot())
        twitch_task = asyncio.create_task(run_twitch_bot())

        plugin_manager = PluginManager()
        plugin_manager.load_plugins()
        await plugin_manager.initialize_plugins(bot)

        await asyncio.gather(sync_task, discord_task, twitch_task)
    except asyncio.CancelledError:
        logger.info("Main task was cancelled.")
    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
    finally:
        await bot.close()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All tasks have been cancelled and cleaned up.")

async def shutdown(signal, loop):
    log_info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    log_info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
        log_info("Successfully shutdown the Aqua Prime bot.")

# Add this function to log commands asynchronously
async def log_command(command):
    async with aiofiles.open('game_commands.log', mode='a') as f:
        await f.write(f"{command}\n")

async def init_discord_bot():
    await bot.add_cog(DiscordBot(bot))
    logger.info("Discord bot initialized")