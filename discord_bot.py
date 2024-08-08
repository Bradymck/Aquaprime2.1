import os
import logging
import discord
from discord import Intents, app_commands
from discord.ext import commands as discord_commands
from database import session_scope, UserEngagement
from utils import process_message_with_context, save_message, get_relevant_summary
from api_client import fetch_recent_conversations

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID')

if not DISCORD_TOKEN:
    raise ValueError("No DISCORD_TOKEN found. Please set it in the environment variables.")
if not DISCORD_GUILD_ID:
    raise ValueError("No DISCORD_GUILD_ID found. Please set it in the environment variables.")

# Discord Bot Setup
intents = Intents.default()
intents.message_content = True
discord_bot = discord_commands.Bot(command_prefix="!", intents=intents)

class DiscordBot(discord_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}
        self.test_guild_id = discord.Object(id=int(DISCORD_GUILD_ID))
        logger.info("DiscordBot cog initialized")

    @app_commands.command(name='chat', description='Chat with the AI and interact with the story')
    @discord_commands.cooldown(1, 5, discord_commands.BucketType.user)
    async def chat(self, interaction: discord.Interaction, message: str):
        user_id = str(interaction.user.id)
        conversation_id = self.conversations.get(user_id)
        if not conversation_id:
            logger.info(f"No conversation ID found for user {user_id}, initializing new conversation.")
            conversation_id = None

        try:
            # Defer the response to allow more time for processing
            await interaction.response.defer()

            relevant_summary = get_relevant_summary(user_id)
            summary_context = f"Recent story summary: {relevant_summary.content}" if relevant_summary else "No recent story summary available."

            prompt = f"{summary_context}\n\nUser message: {message}\n\nPlease respond in the context of the ongoing story:"

            # Log the prompt being sent to OpenAI
            logger.info(f"Generated prompt for OpenAI: {prompt}")

            ai_response = await process_message_with_context(prompt, user_id, 'discord', conversation_id)

            response = f"AI: {ai_response}\n\n"
            if relevant_summary:
                response += f"*Story context: {relevant_summary.content[:100]}...*"

            await interaction.followup.send(response)
            await save_message(message, 'discord', user_id, interaction.user.name)
        except Exception as e:
            logger.error(f"Error in chat command: {e}")
            try:
                await interaction.followup.send("Sorry, an error occurred while processing your request.", ephemeral=True)
            except Exception as followup_error:
                logger.error(f"Failed to send follow-up error message: {followup_error}")

    @app_commands.command(name='reputation', description='Check your reputation')
    async def check_reputation(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            with session_scope() as session:
                user = session.query(UserEngagement).filter_by(user_id=user_id).first()
                if user:
                    await interaction.response.send_message(f"Your current reputation is: {user.reputation}")
                else:
                    await interaction.response.send_message("You don't have any reputation yet.")
        except Exception as e:
            logger.error(f"Error in check_reputation command: {e}")
            await interaction.response.send_message("Sorry, an error occurred while checking your reputation.", ephemeral=True)

    @app_commands.command(name='history', description='View your conversation history')
    async def view_history(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            conversations = await fetch_recent_conversations()
            if conversations:
                history = "\n".join([f"Conversation {i+1}: {conv['summary']}" for i, conv in enumerate(conversations[:5])])
                await interaction.response.send_message(f"Your recent conversations:\n{history}")
            else:
                await interaction.response.send_message("No recent conversations found.")
        except Exception as e:
            logger.error(f"Error in view_history command: {e}")
            await interaction.response.send_message("Sorry, an error occurred while fetching your history.", ephemeral=True)

@discord_bot.event
async def on_ready():
    discord_cog = DiscordBot(discord_bot)
    await discord_bot.add_cog(discord_cog)

    logger.info("Commands in the bot:")
    for command in discord_bot.tree.walk_commands():
        logger.info(f"- {command.name}")

    try:
        logger.info(f"Attempting to sync guild-specific commands for guild {discord_cog.test_guild_id.id}")
        guild_commands = [discord_cog.chat, discord_cog.check_reputation, discord_cog.view_history]
        for cmd in guild_commands:
            discord_bot.tree.add_command(cmd, guild=discord_cog.test_guild_id)
        synced = await discord_bot.tree.sync(guild=discord_cog.test_guild_id)
        logger.info(f'Synced {len(synced)} guild-specific commands to guild {discord_cog.test_guild_id.id}')
        for command in synced:
            logger.info(f"Synced guild-specific command: {command.name}")
    except Exception as e:
        logger.error(f'Failed to sync guild-specific commands: {e}')

    try:
        logger.info("Attempting to sync global commands")
        synced = await discord_bot.tree.sync()
        logger.info(f'Synced {len(synced)} global commands')
    except Exception as e:
        logger.error(f'Failed to sync global commands: {e}')

    logger.info(f'Discord Bot: Logged in as {discord_bot.user}')
    logger.info(f'Discord Bot: In {len(discord_bot.guilds)} guilds')

@discord_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord_commands.errors.CommandNotFound):
        await ctx.send("Command not found. Use !help to see available commands.")
    elif isinstance(error, discord_commands.errors.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
    else:
        logger.error(f"An error occurred: {error}")
        await ctx.send(f"An error occurred: {error}")

@discord_bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    logger.error(f"An error occurred in app command: {error}")
    try:
        if isinstance(error, discord_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
        elif not interaction.response.is_done():
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)
        else:
            logger.warning("Interaction response already done, could not send error message.")
    except discord.errors.NotFound:
        logger.error("Interaction not found, could not send error message (interaction already invalidated).")

async def run_discord_bot():
    try:
        await discord_bot.start(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")

if __name__ == "__main__":
    asyncio.run(run_discord_bot())