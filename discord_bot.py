import os
import logging
import discord
from discord.ext import commands
from game_state_manager import GameStateManager
from utils import process_message_with_context, save_message, get_relevant_summary
from shared_utils import logger, handle_errors

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

game_state_manager = GameStateManager("./AquaPrimeLORE", "./AquaPrimeLORE/game_state.json")

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

async def setup(bot):
    await bot.add_cog(DiscordBot(bot))
async def run_discord_bot():
    await bot.start(os.getenv('DISCORD_TOKEN'))