import logging
from datetime import datetime, timedelta
from database import session_scope, UserEngagement, Message, TranscriptSummary
from textblob import TextBlob
from openai import AsyncOpenAI
import os
from colorama import Fore  # Ensure colorama is imported

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
token = os.environ.get('OPENAI_API_KEY')
if not token:
    logger.error("OpenAI API key is not set.")
client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

def analyze_sentiment(text):
    blob = TextBlob(text)
    # Convert sentiment polarity from -1 to 1 into a scale of 1 to 100
    return int((blob.sentiment.polarity + 1) * 50)  # Scale to 1-100

async def generate_response_with_openai(prompt, user_id):
    try:
        logger.info(f"Sending prompt to OpenAI: {prompt}")
        print(f"{Fore.LIGHTYELLOW_EX}Prompt being sent to OpenAI:\n{prompt}{Fore.RESET}")

        narrative_context = get_narrative_context()
        chat_history = get_chat_history(user_id)
        user_sentiment = get_user_sentiment(user_id)

        # Add emoji based on user sentiment
        sentiment_emoji = "😃" if user_sentiment > 75 else "🙂" if user_sentiment > 50 else "😐" if user_sentiment > 25 else "😞"
        
        full_prompt = (
            f"You are the AI game master (ARI) in Aqua Prime, a TTRPG. "
            f"Your role is to engage the player in character, responding as if you are part of the game world. "
            f"Consider the following:\n"
            f"Narrative Context: {narrative_context}\n"
            f"Recent Chat History: {chat_history}\n"
            f"User Sentiment: {user_sentiment} {sentiment_emoji}\n"
            f"User Message: {prompt}\n"
            f"Respond in character, incorporating the current game state."
        )

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ]
        )
        logger.info(f"OpenAI response: {response}")
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error communicating with OpenAI API: {str(e)}")
        if 'invalid_api_key' in str(e):
            logger.error("Invalid API key. Please check your OpenAI API key in Replit secrets.")
        return "Sorry, I encountered an error while processing your request."

async def process_message_with_context(content, user_id, platform, conversation_id):
    with session_scope() as session:
        past_messages = session.query(Message).filter_by(user_id=user_id).order_by(Message.created_at.desc()).limit(5).all()
        past_messages = [msg.content for msg in past_messages]

        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        user_sentiment = user.overall_sentiment if user else 0.0

    ram_messages = " ".join(past_messages)

    prompt = (f"System Instructions: Handle the following user messages.\n"
              f"User Sentiment: {user_sentiment}\n"
              f"Platform: {platform}\n"
              f"Recent Context: {ram_messages}\n"
              f"User Message: {content}")

    # Log the prompt here
    logger.info(f"Prompt being sent to OpenAI: {prompt}")

    ai_response = await generate_response_with_openai(prompt, user_id)
    return ai_response

async def save_message(content, platform, user_id, username):
    sentiment = analyze_sentiment(content)
    with session_scope() as session:
        new_message = Message(content=content, platform=platform, user_id=user_id, username=username, sentiment=sentiment)
        session.add(new_message)
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        if user:
            user.message_count += 1
            user.last_active = datetime.utcnow()
            user.overall_sentiment = (user.overall_sentiment * (user.message_count - 1) + sentiment) / user.message_count
            user.overall_sentiment = int(user.overall_sentiment)  # Ensure it's an integer
        else:
            new_user = UserEngagement(user_id=user_id, username=username, message_count=1, overall_sentiment=sentiment)
            session.add(new_user)
    logger.info(f"Message saved to database for user {username}")

def get_relevant_summary(user_id, query=None):
    with session_scope() as session:
        latest_summary = session.query(TranscriptSummary).order_by(TranscriptSummary.created_at.desc()).first()
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        last_interaction = user.last_active if user else None

        if last_interaction and latest_summary and latest_summary.created_at > last_interaction:
            return latest_summary.content if latest_summary else None

        return session.query(TranscriptSummary).order_by(TranscriptSummary.created_at.desc()).first()

def update_user_reputations():
    with session_scope() as session:
        users = session.query(UserEngagement).all()
        for user in users:
            if (datetime.utcnow() - user.last_active) <= timedelta(days=7):
                logger.info(f"Updating reputation for user: {user.username}, Role: {user.role}, Sentiment: {user.overall_sentiment}, Current Reputation: {user.reputation}")

                # Ensure reputation is initialized
                if user.reputation is None:
                    user.reputation = 50  # Set a default value if not initialized

                # Reputation update logic based on role
                if user.role == "Black Hat":
                    if user.overall_sentiment > 50:  # Good behavior
                        user.reputation -= 2  # Punish for good behavior
                    else:
                        user.reputation += 2  # Reward for bad behavior
                elif user.role == "White Hat":
                    if user.overall_sentiment < 50:  # Bad behavior
                        user.reputation -= 2  # Punish for bad behavior
                    else:
                        user.reputation += 2  # Reward for good behavior
                elif user.role == "Grey Hat":
                    if user.overall_sentiment > 50:  # Good behavior
                        user.reputation -= 1  # Punish for good behavior
                        user.reputation *= 1.5  # Apply multiplier for Grey Hat
                    else:
                        user.reputation -= 1  # Punish for bad behavior
                        user.reputation *= 1.5  # Apply multiplier for Grey Hat

                # Ensure reputation stays within bounds
                user.reputation = max(0, min(user.reputation, 100))
                logger.info(f"New Reputation for user: {user.username}, Updated Reputation: {user.reputation}")

def get_user_reputation(user_id):
    with session_scope() as session:
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        if user:
            logger.info(f"Retrieved Reputation for User: {user.username}, Reputation: {user.reputation}")
            return user.reputation
        return None

async def periodic_summarization(agent_id, api_key, user_id):
    # This function should be implemented to periodically create summaries
    # of recent conversations and store them in the TranscriptSummary table
    pass

async def summarize_transcripts(transcripts):
    # This function should be implemented to create summaries from the provided transcripts
    # It should use the OpenAI API to generate summaries
    pass

def get_narrative_context():
    # Retrieve relevant game lore or current narrative elements
    return "Current events: Faction Wars are ongoing, and the ARI is guiding players through challenges."

def get_chat_history(user_id):
    with session_scope() as session:
        past_messages = session.query(Message).filter_by(user_id=user_id).order_by(Message.created_at.desc()).limit(5).all()
        return " ".join(msg.content for msg in past_messages)

def get_user_sentiment(user_id):
    with session_scope() as session:
        user = session.query(UserEngagement).filter_by(user_id=user_id).first()
        return user.overall_sentiment if user else 0.0

import discord
import os

# Create an instance of Intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.content == '!shutdown':
        await shutdown_bot()
    elif message.content.startswith('/reputation'):
        user_id = message.author.id
        reputation = get_user_reputation(user_id)
        if reputation is not None:
            await message.channel.send(f"Your current reputation is: {reputation}")
        else:
            await message.channel.send("Could not retrieve your reputation.")

async def shutdown_bot():
    print("Shutting down...")
    await client.close()

async def run_discord_bot():
    token = os.environ.get('DISCORD_TOKEN')
    print(f"Using token: {token}")  # Debugging line
    await client.start(token)

import asyncio

def main():
    from discord_bot import run_discord_bot  # Import here to avoid circular import

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(run_discord_bot())
    finally:
        loop.close()

if __name__ == "__main__":
    main()