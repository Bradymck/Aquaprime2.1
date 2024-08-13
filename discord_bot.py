import os
import logging
import discord
from discord.ext import commands
from game_state_manager import GameStateManager
from utils import process_message_with_context, save_message, get_relevant_summary
from shared_utils import logger, handle_errors
from config import initialize_openai_client
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=os.getenv('DISCORD_APPLICATION_ID')
)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.tree.sync()

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

            if not interaction.response.is_done():
                await interaction.response.send_message(response)
            else:
                await interaction.followup.send(response)

            await save_message(message, 'discord', user_id, interaction.user.name, is_user=True)
            await save_message(ai_response, 'discord', user_id, 'AI', is_user=False)

            game_state_manager.update_agent_knowledge(user_id, {"question": message, "answer": ai_response})

        except Exception as e:
            logger.error(f"Chat error for user {user_id}: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("An error occurred while processing your request.")
            else:
                await interaction.followup.send("An error occurred while processing your request.")

    @discord.app_commands.command(name='help', description='Display available commands')
    async def help_command(self, interaction: discord.Interaction):
        commands = [
            ('chat', 'Chat with the AI'),
            ('faction_info', 'Get information about your faction'),
            ('game_status', 'Check the current game status')
        ]
        help_text = "\n".join([f"!{cmd}: {desc}" for cmd, desc in commands])
        await interaction.response.send_message(f"Available commands:\n{help_text}")

async def run_discord_bot():
    try:
        await bot.add_cog(DiscordBot(bot))
        await bot.start(os.getenv('DISCORD_BOT_TOKEN'))
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()