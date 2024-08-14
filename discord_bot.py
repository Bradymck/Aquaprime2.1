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

class ChatCommand(discord.app_commands.Command):
    def __init__(self, bot):
        super().__init__(name="chat", description="Chat with the AI", callback=self.chat_callback)
        self.bot = bot

    async def chat_callback(self, interaction: discord.Interaction, message: str):
        # Defer the response immediately
        await interaction.response.defer(thinking=True)
        
        try:
            # Process the message
            response = await process_message_with_context(message, str(interaction.user.id), "discord", None)
            
            # Send the response
            await interaction.followup.send(response)
        except Exception as e:
            # Log the error
            logger.error(f"Error in chat: {str(e)}")
            
            # Send an error message
            await interaction.followup.send("An error occurred while processing your request. Please try again later.")

bot.tree.add_command(ChatCommand(bot))

async def run_discord_bot():
    try:
        await bot.start(os.getenv('DISCORD_BOT_TOKEN'))
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()