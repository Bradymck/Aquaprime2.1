import os
import logging
from twitchio.ext import commands
import asyncio
from utils import process_message_with_context, save_message, get_relevant_summary
from shared_utils import logger
from aiolimiter import AsyncLimiter  # Import AsyncLimiter

required_env_vars = [
    'TWITCH_IRC_TOKEN', 'TWITCH_CLIENT_ID', 'TWITCH_CHANNEL', 'TWITCH_NICK',
    'PLAY_AI_API_KEY', 'PLAY_AI_USER_ID', 'AGENT_ID', 'PLAY_AI_API_URL', 'OPENAI_API_KEY'
]

# Rate limiter: 5 commands per minute
rate_limiter = AsyncLimiter(5, 60)

class Bot(commands.Bot):
    def __init__(self):
        # Check for required environment variables
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        super().__init__(
            token=os.getenv('TWITCH_IRC_TOKEN'),
            client_id=os.getenv('TWITCH_CLIENT_ID'),
            nick=os.getenv('TWITCH_NICK'),
            prefix='!',
            initial_channels=[os.getenv('TWITCH_CHANNEL')]
        )
        self.conversations = {}

    async def event_ready(self):
        logger.info(f"Logged in as | {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return

        logger.info(f"Message from {message.author.name}: {message.content[:50]}...")

        user_id = str(message.author.id)
        await save_message(message.content, 'twitch', user_id, message.author.name)

        if message.content.startswith('!'):
            await self.handle_commands(message)

    @commands.command(name="chat")
    async def chat_command(self, ctx: commands.Context, *, message: str):
        async with rate_limiter:  # Use the rate limiter
            user_id = str(ctx.author.id)
            conversation_id = self.conversations.get(user_id)

            try:
                relevant_summary = get_relevant_summary(user_id)
                summary_context = f"Recent story summary: {relevant_summary}" if relevant_summary else "No recent story summary available."

                prompt = f"{summary_context}\n\nUser message: {message}\n\nPlease respond in the context of the ongoing story:"
                ai_response = await process_message_with_context(prompt, user_id, 'twitch', conversation_id)

                response = f"AI: {ai_response}"
                if relevant_summary:
                    response += f"\n*Story context: {relevant_summary[:100]}..."

                await ctx.send(response)
                logger.info(f"Successful chat interaction with user {user_id}")
            except Exception as e:
                logger.error(f"Error in Twitch chat command for user {user_id}: {e}")
                await ctx.send("Sorry, an error occurred while processing your request.")

    @commands.command(name="recite")
    async def recite_command(self, ctx: commands.Context, *, query: str = None):
        try:
            summary = get_relevant_summary(str(ctx.author.id), query)
            if summary:
                await ctx.send(f"Summary: {summary}")
                logger.info(f"Summary retrieved for user {ctx.author.id}")
            else:
                await ctx.send("Sorry, I couldn't find any relevant summary.")
                logger.info(f"No summary found for user {ctx.author.id}")
        except Exception as e:
            logger.error(f"Error in Twitch recite command for user {ctx.author.id}: {e}")
            await ctx.send("Sorry, an error occurred while retrieving the summary.")

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        help_text = """
        Available Aqua Prime commands:
        !chat <message>: Chat with the AI
        !recite [query]: Get a summary related to your query or your latest interaction
        !help: Show this help message
        """
        await ctx.send(help_text)
        logger.info(f"Help command used by user {ctx.author.id}")

    async def log_twitch_activity(self, activity):
        async with aiofiles.open('twitch_activity.log', mode='a') as f:
            await f.write(f"{activity}\n")

    async def close(self):
        await super().close()
        logger.info("Twitch bot closed")

async def run_twitch_bot():
    try:
        logger.info("Aqua Prime Twitch Bot Starting")
        bot = Bot()
        await bot.start()
    except Exception as e:
        logger.error(f"Error running Twitch bot: {e}")
    finally:
        logger.info("Twitch bot closed")

async def main():
    try:
        twitch_task = asyncio.create_task(run_twitch_bot())
        await twitch_task
    except asyncio.CancelledError:
        logger.info("Main task cancelled, cancelling Twitch bot task.")
        twitch_task.cancel()
        await twitch_task  # Ensure the task is awaited after cancellation
    except Exception as e:
        logger.error(f"Unexpected error running Twitch bot: {e}")

if __name__ == "__main__":
    logger.info("Aqua Prime Twitch Bot Starting")
    asyncio.run(main())