import os
import logging
from twitchio.ext import commands
from database import session_scope, UserEngagement, get_latest_summary, get_relevant_summary
from utils import process_message_with_context, save_message
from api_client import fetch_recent_conversations, get_latest_summary, get_relevant_summary

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')

# Load environment variables
TWITCH_IRC_TOKEN = os.getenv('TWITCH_IRC_TOKEN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CHANNEL = os.getenv('TWITCH_CHANNEL')
TWITCH_NICK = os.getenv('TWITCH_NICK')

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=TWITCH_IRC_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_NICK,
            prefix='!',
            initial_channels=[TWITCH_CHANNEL]
        )
        self.conversations = {}

    async def event_ready(self):
        logger.info(f'Twitch Bot: Logged in as | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return

        logger.info(f"Message from {message.author.name}: {message.content}")

        user_id = str(message.author.id)
        await save_message(message.content, 'twitch', user_id, message.author.name)

        if message.content.startswith('!'):
            await self.handle_commands(message)

    @commands.command(name="chat")
    async def chat_command(self, ctx: commands.Context, *, message: str):
        user_id = str(ctx.author.id)
        conversation_id = self.conversations.get(user_id)

        try:
            relevant_summary = get_relevant_summary(user_id)
            summary_context = f"Recent story summary: {relevant_summary.content}" if relevant_summary else "No recent story summary available."

            prompt = f"{summary_context}\n\nUser message: {message}\n\nPlease respond in the context of the ongoing story:"

            ai_response = await process_message_with_context(prompt, user_id, 'twitch', conversation_id)

            response = f"AI: {ai_response}"
            if relevant_summary:
                response += f"\n*Story context: {relevant_summary.content[:100]}...*"

            await ctx.send(response)
        except Exception as e:
            logger.error(f"Error in Twitch chat command: {e}")
            await ctx.send("Sorry, an error occurred while processing your request.")

    @commands.command(name="reputation")
    async def check_reputation(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        try:
            with session_scope() as session:
                user = session.query(UserEngagement).filter_by(user_id=user_id).first()
                if user:
                    await ctx.send(f"@{ctx.author.name}, your current reputation is: {user.reputation}")
                else:
                    await ctx.send(f"@{ctx.author.name}, you don't have any reputation yet.")
        except Exception as e:
            logger.error(f"Error in Twitch check_reputation command: {e}")
            await ctx.send("Sorry, an error occurred while checking your reputation.")

    @commands.command(name="history")
    async def view_history(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        try:
            conversations = await fetch_recent_conversations()
            if conversations:
                history = "\n".join([f"Conversation {i+1}: {conv['summary']}" for i, conv in enumerate(conversations[:5])])
                await ctx.send(f"@{ctx.author.name}, your recent conversations:\n{history}")
            else:
                await ctx.send(f"@{ctx.author.name}, no recent conversations found.")
        except Exception as e:
            logger.error(f"Error in Twitch view_history command: {e}")
            await ctx.send("Sorry, an error occurred while fetching your history.")

    @commands.command(name="recite")
    async def recite_command(self, ctx: commands.Context, *, query: str = None):
        try:
            with session_scope() as session:
                if query:
                    summary = get_relevant_summary(session, query)
                else:
                    summary = get_latest_summary(session)

            if summary:
                await ctx.send(f"Summary: {summary}")
            else:
                await ctx.send("Sorry, I couldn't find any relevant summary.")
        except Exception as e:
            logger.error(f"Error in Twitch recite command: {e}")
            await ctx.send("Sorry, an error occurred while retrieving the summary.")

async def run_twitch_bot():
    twitch_bot = TwitchBot()
    try:
        await twitch_bot.start()
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")

if __name__ == "__main__":
    asyncio.run(run_twitch_bot())