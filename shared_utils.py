import discord
from discord.ext import commands as discord_commands
from discord import app_commands  # Add this line
import logging
import os
from colorama import init, Fore, Back, Style
from openai import AsyncOpenAI  # Ensure this is imported

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Set up logger
logger = logging.getLogger('UnifiedBot')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def print_header(message):
    print(f"{Fore.CYAN}=== {message} ==={Style.RESET_ALL}")

# Expanded COLORS dictionary
COLORS = {
    'header': Fore.WHITE + Back.BLUE,
    'info': Fore.BLACK + Back.CYAN,
    'success': Fore.BLACK + Back.GREEN,
    'warning': Fore.BLACK + Back.YELLOW,
    'error': Fore.WHITE + Back.RED,
    'reset': Style.RESET_ALL
}

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Use AsyncOpenAI

# Create the bot instance
intents = discord.Intents.default()
intents.message_content = True  # Ensure you have the right intents
discord_bot = discord_commands.Bot(command_prefix="!", intents=intents)

# Your DiscordBot class and other commands go here
class DiscordBot(discord_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}
        self.test_guild_id = discord.Object(id=int(os.getenv('DISCORD_GUILD_ID')))
        logger.info("DiscordBot initialized")

    @app_commands.command(name='chat', description='Chat with the AI')
    @discord_commands.cooldown(1, 5, discord_commands.BucketType.user)
    async def chat(self, interaction: discord.Interaction, message: str):
        user_id = str(interaction.user.id)
        
        # Check if the user already has a conversation ID
        if user_id not in self.conversations:
            # Create a new conversation ID and store it
            conversation_id = f"conv_{user_id}_{int(datetime.utcnow().timestamp())}"
            self.conversations[user_id] = conversation_id
            logger.info(f"Created new conversation ID for user {user_id}: {conversation_id}")
        else:
            conversation_id = self.conversations[user_id]

        # The rest of your chat logic...

# Register the DiscordBot cog
discord_bot.add_cog(DiscordBot(discord_bot))

@discord_bot.event
async def on_ready():
    logger.info(f'Logged in as {discord_bot.user.name} (ID: {discord_bot.user.id})')
    logger.info('------')

async def run_discord_bot():
    try:
        await discord_bot.start(os.environ['DISCORD_TOKEN'])
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")

if __name__ == "__main__":
    print_header("Aqua Prime Discord Bot Starting")
    asyncio.run(run_discord_bot())