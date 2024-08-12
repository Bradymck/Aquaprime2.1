import os
import logging
from twitchio.ext import commands
import asyncio
from colorama import Fore, Style
from utils import process_message_with_context, save_message, get_relevant_summary
from shared_utils import logger, print_header, COLORS
# Aqua Prime themed emojis
AQUA_EMOJIS = ["🌊", "💧", "🐠", "🐳", "🦈", "🐙", "🦀", "🐚", "🏊‍♂️", "🏄‍♂️", "🤿", "🚤"]
required_env_vars = [
    'TWITCH_IRC_TOKEN', 'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK',
    'PLAY_AI_API_KEY', 'PLAY_AI_USER_ID', 'AGENT_ID', 'PLAY_AI_API_URL', 'OPENAI_API_KEY'
]
import aiofiles  # Add this import

class RateLimiter:
    def __init__(self, rate, per):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = asyncio.get_event_loop().time()
    async def is_allowed(self):
        current = asyncio.get_event_loop().time()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * (self.rate / self.per)
        if self.allowance > self.rate:
            self.allowance = self.rate
        if self.allowance < 1:
            return False
        self.allowance -= 1
        return True

class Bot(commands.Bot):
    def __init__(self):
        # Check for required environment variables
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"🚫 Missing required environment variables: {', '.join(missing_vars)}")

        super().__init__(
            token=os.getenv('TWITCH_IRC_TOKEN'),
            client_id=os.getenv('TWITCH_CLIENT_ID'),
            nick=os.getenv('TWITCH_NICK'),
            prefix='!',
            initial_channels=[os.getenv('TWITCH_CHANNEL')]
        )
        self.rate_limiter = RateLimiter(rate=5, per=60)  # 5 commands per minute
        self.conversations = {}

    async def event_ready(self):
        logger.info(f"🎮 Logged in as | {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        logger.info(f"📨 Message from {message.author.name}: {message.content[:50]}...")

        user_id = str(message.author.id)
        await save_message(message.content, 'twitch', user_id, message.author.name)

        if message.content.startswith('!'):
            await self.handle_commands(message)

    @commands.command(name="chat")
    async def chat_command(self, ctx: commands.Context, *, message: str):
        if not await self.rate_limiter.is_allowed():
            await ctx.send("⏳ You're sending commands too quickly. Please wait a moment.")
            return

        user_id = str(ctx.author.id)
        conversation_id = self.conversations.get(user_id)

        try:
            relevant_summary = get_relevant_summary(user_id)
            summary_context = f"Recent story summary: {relevant_summary}" if relevant_summary else "No recent story summary available."

            prompt = f"{summary_context}\n\nUser message: {message}\n\nPlease respond in the context of the ongoing story:"

            ai_response = await process_message_with_context(prompt, user_id, 'twitch', conversation_id)

            response = f"🤖 AI: {ai_response}"
            if relevant_summary:
                response += f"\n📜 *Story context: {relevant_summary[:100]}...*"

            await ctx.send(response)
            logger.info(f"💬 Successful chat interaction with user {user_id}")
        except Exception as e:
            logger.error(f"🚫 Error in Twitch chat command for user {user_id}: {e}")
            await ctx.send("🚫 Sorry, an error occurred while processing your request.")

    @commands.command(name="recite")
    async def recite_command(self, ctx: commands.Context, *, query: str = None):
        try:
            summary = get_relevant_summary(str(ctx.author.id), query)
            if summary:
                await ctx.send(f"📚 Summary: {summary}")
                logger.info(f"📜 Summary retrieved for user {ctx.author.id}")
            else:
                await ctx.send("📭 Sorry, I couldn't find any relevant summary.")
                logger.info(f"📜 No summary found for user {ctx.author.id}")
        except Exception as e:
            logger.error(f"🚫 Error in Twitch recite command for user {ctx.author.id}: {e}")
            await ctx.send("🚫 Sorry, an error occurred while retrieving the summary.")

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        help_text = """
        🌊 Available Aqua Prime commands:
        !chat <message>: 💬 Chat with the AI
        !recite [query]: 📚 Get a summary related to your query or your latest interaction
        !help: ℹ️ Show this help message
        """
        await ctx.send(help_text)
        logger.info(f"ℹ️ Help command used by user {ctx.author.id}")

    async def log_twitch_activity(self, activity):
        async with aiofiles.open('twitch_activity.log', mode='a') as f:
            await f.write(f"{activity}\n")

    async def close(self):
        await super().close()
        logger.info("🛑 Twitch bot closed")

async def run_twitch_bot():
    try:
        print_header("Aqua Prime Twitch Bot Starting")
        bot = Bot()
        await bot.start()
    except ValueError as e:
        logger.error(f"🚫 Error initializing Twitch bot: {e}")
    except Exception as e:
        logger.error(f"🚫 Unexpected error running Twitch bot: {e}")
    finally:
        print_header("Aqua Prime Twitch Bot Shutdown")

if __name__ == "__main__":
    print(f"\n{COLORS['header']}{'=' * 80}{COLORS['reset']}")
    print(f"{COLORS['header']}{'Aqua Prime Twitch Bot Starting':^80}{COLORS['reset']}")
    print(f"{COLORS['header']}{'=' * 80}{COLORS['reset']}\n")

    asyncio.get_event_loop().run_until_complete(run_twitch_bot())