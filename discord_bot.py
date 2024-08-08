import os
import logging
import discord
import random
import asyncio
from discord import Intents, app_commands
from discord.ext import commands as discord_commands
from colorama import init, Fore, Back, Style
from database import session_scope, UserEngagement
from utils import process_message_with_context, save_message, get_relevant_summary
from api_client import fetch_recent_conversations
from shared_utils import logger

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

        log_message = record.getMessage()  # Corrected method
        return f"{log_color}{log_message:<80}{COLORS['reset']}"

# Set up logging
logger = logging.getLogger('discord_bot')
handler = logging.StreamHandler()
handler.setFormatter(AquaPrimeFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
DISCORD_GUILD_ID = os.environ['DISCORD_GUILD_ID']

if not DISCORD_TOKEN:
    raise ValueError("No DISCORD_TOKEN found.")
if not DISCORD_GUILD_ID:
    raise ValueError("No DISCORD_GUILD_ID found.")

intents = Intents.default()
intents.message_content = True
discord_bot = discord_commands.Bot(command_prefix="!", intents=intents)

class DiscordBot(discord_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}
        self.test_guild_id = discord.Object(id=int(DISCORD_GUILD_ID))
        logger.info("DiscordBot initialized")

    @app_commands.command(name='chat', description='Chat with the AI')
    @discord_commands.cooldown(1, 5, discord_commands.BucketType.user)
    async def chat(self, interaction: discord.Interaction, message: str):
        user_id = str(interaction.user.id)
        conversation_id = self.conversations.get(user_id)
        if not conversation_id:
            logger.info(f"No conversation ID for user {user_id}.")
            conversation_id = None

        try:
            relevant_summary = get_relevant_summary(user_id)
            summary_context = f"Summary: {relevant_summary.content}" if relevant_summary else "No summary available."

            prompt = f"{summary_context}\n\nUser: {message}\n\n"

            ai_response = await process_message_with_context(prompt, user_id, 'discord', conversation_id)
            response = f"AI: {ai_response}\n"
            if relevant_summary:
                response += f"Context: {relevant_summary[:100]}..."

            await interaction.response.send_message(response)
            await save_message(message, 'discord', user_id, interaction.user.name)
            logger.info(f"Chat with user {user_id} successful")
        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}")
            await interaction.response.send_message("Error.", ephemeral=True)

    @app_commands.command(name='reputation', description='Check your reputation')
    async def check_reputation(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            with session_scope() as session:
                user = session.query(UserEngagement).filter_by(user_id=user_id).first()
                if user:
                    await interaction.response.send_message(f"Your reputation: {user.reputation}")
                    logger.info(f"Reputation check for user {user_id}")
                else:
                    await interaction.response.send_message("No reputation yet.")
        except Exception as e:
            logger.error(f"Reputation error for user {user_id}: {e}")
            await interaction.response.send_message("Error.", ephemeral=True)

    @app_commands.command(name='history', description='View your history')
    async def view_history(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            conversations = await fetch_recent_conversations()
            if conversations:
                history = "\n".join([f"Conversation {i+1}: {conv['summary']}" for i, conv in enumerate(conversations[:5])])
                await interaction.response.send_message(f"Your conversations:\n{history}")
                logger.info(f"History for user {user_id}")
            else:
                await interaction.response.send_message("No conversations found.")
        except Exception as e:
            logger.error(f"History error for user {user_id}: {e}")
            await interaction.response.send_message("Error.", ephemeral=True)

@discord_bot.event
async def on_message(message):
    if message.author == discord_bot.user:
        return

    logger.info(f"Message from {message.author.name}: {message.content[:50]}...")
    await discord_bot.process_commands(message)

@discord_bot.event
async def on_ready():
    discord_cog = DiscordBot(discord_bot)
    await discord_bot.add_cog(discord_cog)

    print_header("Aqua Prime Discord Bot Starting")

    log_info("Aqua Prime Database Initialized", emoji='🦈')
    log_info("Replit secrets set: DISCORD_TOKEN, DISCORD_GUILD_ID, TWITCH_IRC_TOKEN, TWITCH_CLIENT_ID, TWITCH_CHANNEL, TWITCH_NICK, OPENAI_API_KEY")
    log_info("Aqua Prime Bot Initializing")
    
    print_header("Commands")
    log_info("Guild commands: • chat • reputation • history")
    log_info("Global commands: • None")
    
    log_info(f"Latency: {Fore.YELLOW}{Style.BRIGHT}26.94ms")

@discord_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord_commands.errors.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, discord_commands.errors.CommandOnCooldown):
        await ctx.send(f"Cooldown. Try again in {error.retry_after:.2f} seconds.")
    else:
        logger.error(f"Error: {error}")
        await ctx.send(f"Error: {error}")

@discord_bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    logger.error(f"App command error: {error}")
    try:
        if isinstance(error, discord_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(f"Cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
        elif not interaction.response.is_done():
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)
        else:
            logger.warning("Response already sent.")
    except discord.errors.NotFound:
        logger.error("Interaction not found.")

async def run_discord_bot():
    try:
        await discord_bot.start(os.environ['DISCORD_TOKEN'])
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")

if __name__ == "__main__":
    print_header("Aqua Prime Discord Bot Starting")
    asyncio.run(run_discord_bot())

def print_header(message):
    # Print a formatted header with borders and colors
    border = "=" * (len(message) + 4)
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{border}")
    print(f"{Fore.CYAN}{Style.BRIGHT}|| {message} ||")
    print(f"{Fore.CYAN}{Style.BRIGHT}{border}\n")

def log_info(message, emoji='🐳'):
    logging.info(f"{emoji} {Fore.GREEN}{Style.BRIGHT}{message}")