# discord_bot.py

import os
import logging
import discord
from discord import app_commands
from discord.ext import commands as discord_commands
from colorama import init, Fore, Back, Style
from database import session_scope, UserEngagement
from utils import process_message_with_context, save_message, get_relevant_summary
from api_client import update_agent_knowledge, fetch_recent_conversations
from game_state_manager import GameStateManager
from shared_utils import logger
from kb_manager import KBManager
from datetime import datetime
import json
import traceback
from discord import Intents
import asyncio

init(autoreset=True)

# Correct the paths to point to the AquaPrimeLORE directory
repo_path = "./AquaPrimeLORE"
file_path = "./AquaPrimeLORE/game_state.json"
game_state_manager = GameStateManager(repo_path, file_path)

# Properly initialize the bot using discord_commands.Bot
intents = Intents.default()
intents.message_content = True  # Update for needed intent
bot = discord_commands.Bot(command_prefix="!", intents=intents)

class DiscordBot(discord_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}
        self.test_guild_id = discord.Object(id=int(os.getenv('DISCORD_GUILD_ID')))
        logger.info("DiscordBot initialized")
    @discord_commands.command(name='chat', description='Chat with the AI')
    async def chat(self, interaction: discord.Interaction, message: str):
        user_id = str(interaction.user.id)
        conversation_id = self.conversations.get(user_id)
        if not conversation_id:
            logger.info(f"No conversation ID for user {user_id}.")
            conversation_id = None

        try:
            relevant_summary = get_relevant_summary(user_id)
            summary_context = f"Summary: {relevant_summary}" if relevant_summary else "No summary available."

            prompt = f"{summary_context}\n\nUser: {message}\n\n"
            ai_response = await process_message_with_context(prompt, user_id, 'discord', conversation_id)
            response = f"AI: {ai_response}\n"
            if relevant_summary:
                response += f"Context: {relevant_summary[:100]}..."

            await interaction.response.send_message(response)
            await save_message(message, 'discord', user_id, interaction.user.name)
            logger.info(f"Chat with user {user_id} successful")

            from api_client import update_agent_knowledge  # Move import here
            await update_agent_knowledge(os.getenv('AGENT_ID'), {"question": message, "answer": ai_response})

            new_memory = {"timestamp": str(datetime.now()), "description": f"User: {message}, AI: {ai_response}"}
            game_state_manager.update_state(new_memory)  # Ensure this method exists in GameStateManager

        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}")
            await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)

@bot.event
async def on_ready():
    discord_cog = DiscordBot(bot)
    await bot.add_cog(discord_cog)
    logger.info("Aqua Prime Discord Bot Starting")
logger.info(f"Available commands: {[command.name for command in bot.tree.get_commands()]}")
async def run_discord_bot():
    try:
        await bot.start(os.environ['DISCORD_TOKEN'])
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")

if __name__ == "__main__":
    asyncio.run(run_discord_bot())