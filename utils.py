import logging
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Set up logger
logger = logging.getLogger('UnifiedBot')
logging.basicConfig(level=logging.WARNING,  # Change to WARNING to reduce log verbosity
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

def log_info(message):
    logger.info(f"{COLORS['info']}{message}{COLORS['reset']}")

def log_success(message):
    logger.info(f"{COLORS['success']}{message}{COLORS['reset']}")

def log_warning(message):
    logger.warning(f"{COLORS['warning']}{message}{COLORS['reset']}")

def log_error(message):
    logger.error(f"{COLORS['error']}{message}{COLORS['reset']}")


# Example usage
if __name__ == "__main__":
    print_header("Aqua Prime Bot Initialization")
    log_info("Bot is starting...")
    log_success("Successfully connected to the database.")
    log_warning("This is a warning message.")
    log_error("This is an error message.")

    prompt = (f"System Instructions: Handle the following user messages.\n"
              f"User Sentiment: {user_sentiment}\n"
              f"Platform: {platform}\n"
              f"Recent Context: {ram_messages}\n"
              f"User Message: {content}")

    # Log the prompt here
    logger.info(f"Prompt being sent to OpenAI: {prompt}")

    ai_response = await generate_response_with_openai(prompt)
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
                user.reputation += 1
            if user.overall_sentiment > 0.5:
                user.reputation += 2
            elif user.overall_sentiment < -0.5:
                user.reputation -= 1
            user.reputation = max(0, min(user.reputation, 100))
    logger.info("User reputations updated")

def purge_old_messages(days_to_keep=30):
    with session_scope() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = session.query(Message).filter(Message.created_at < cutoff_date).delete()
        logger.info(f"Purged {deleted} messages older than {days_to_keep} days")

async def periodic_summarization(agent_id, api_key, user_id):
    # This function should be implemented to periodically create summaries
    # of recent conversations and store them in the TranscriptSummary table
    pass

async def summarize_transcripts(transcripts):
    # This function should be implemented to create summaries from the provided transcripts
    # It should use the OpenAI API to generate summaries
    pass

