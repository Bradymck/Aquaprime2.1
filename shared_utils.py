import logging
import os  # Add this import statement
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
        
        # Check if the user already has a conversation ID
        if user_id not in self.conversations:
            # Create a new conversation ID and store it
            conversation_id = f"conv_{user_id}_{int(datetime.utcnow().timestamp())}"
            self.conversations[user_id] = conversation_id
            logger.info(f"Created new conversation ID for user {user_id}: {conversation_id}")
        else:
            conversation_id = self.conversations[user_id]

        # The rest of your chat logic...

def get_relevant_summary(user_id, query=None):
    logger.info(f"Fetching relevant summary for user {user_id}")
    with session_scope() as session:
        latest_summary = session.query(TranscriptSummary).order_by(TranscriptSummary.created_at.desc()).first()
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        last_interaction = user.last_active if user else None

        if last_interaction and latest_summary and latest_summary.created_at > last_interaction:
            return latest_summary.content if latest_summary else None

        # Return the latest summary if no recent interaction
        return latest_summary.content if latest_summary else None