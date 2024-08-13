import os
import logging
import discord
from discord.ext import commands
from game_state_manager import GameStateManager
from utils import process_message_with_context, save_message, get_relevant_summary
from shared_utils import logger, handle_errors
from config import initialize_openai_client

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

game_state_manager = GameStateManager("./AquaPrimeLORE", "./AquaPrimeLORE/game_state.json")
openai_client = initialize_openai_client()

class DiscordBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name='chat', description='Chat with the AI')
    @handle_errors
    async def chat(self, interaction: discord.Interaction, *, message: str):
        user_id = str(interaction.user.id)
        conversation_id = f"discord_{interaction.channel_id}"

        try:
            ai_response = await process_message_with_context(message, user_id, 'discord', conversation_id)
            response = f"AI: {ai_response}\n"

            await interaction.response.send_message(response)
            await save_message(message, 'discord', user_id, interaction.user.name, is_user=True)
            await save_message(ai_response, 'discord', user_id, 'AI', is_user=False)

            game_state_manager.update_agent_knowledge(user_id, {"question": message, "answer": ai_response})

        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}")
            await interaction.response.send_message("An error occurred while processing your request.")

    @discord.app_commands.command(name='help', description='Display available commands')
    async def help_command(self, interaction: discord.Interaction):
        commands = [
            ('chat', 'Chat with the AI'),
            ('faction_info', 'Get information about your faction'),
            ('game_status', 'Check the current game status')
        ]
        help_text = "\n".join([f"!{cmd}: {desc}" for cmd, desc in commands])
        await interaction.response.send_message(f"Available commands:\n{help_text}")

    @discord.app_commands.command(name='faction_info', description='Get information about your faction')
    @handle_errors
    async def faction_info(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            faction_info = game_state_manager.get_faction_info(user_id)
            await interaction.response.send_message(f"Your faction info: {faction_info}")
        except Exception as e:
            logger.error(f"Error fetching faction info for user {user_id}: {e}")
            await interaction.response.send_message("An error occurred while fetching faction information.")

    @discord.app_commands.command(name='game_status', description='Check the current game status')
    @handle_errors
    async def game_status(self, interaction: discord.Interaction):
        try:
            status = game_state_manager.get_game_status()
            await interaction.response.send_message(f"Current game status: {status}")
        except Exception as e:
            logger.error(f"Error fetching game status: {e}")
            await interaction.response.send_message("An error occurred while fetching game status.")

async def run_discord_bot():
    try:
        await bot.add_cog(DiscordBot(bot))
        await bot.start(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()