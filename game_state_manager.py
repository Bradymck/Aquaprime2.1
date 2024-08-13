import json
import aiohttp
import asyncio
from shared_utils import logger

class GameStateManager:
    def __init__(self, repo_path, file_path):
        self.repo_path = repo_path
        self.file_path = file_path
        self.game_state = self.load_game_state()
        self.knowledge_base = {}  # Initialize knowledge base

    def load_game_state(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def add_knowledge(self, key, value):
        self.knowledge_base[key] = value

    def get_knowledge(self, key):
        return self.knowledge_base.get(key, None)

    def remove_knowledge(self, key):
        if key in self.knowledge_base:
            del self.knowledge_base[key]

    def clear_knowledge(self):
        self.knowledge_base.clear()

    def list_knowledge_entries(self):
        return self.knowledge_base.items()

    def summarize_transcript(self, transcript):
        # Implement your summarization logic here
        summary = "Summary of the transcript"  # Placeholder
        self.add_knowledge(transcript['id'], summary)  # Store summary in knowledge base
        return summary

    async def update_agent(self, agent_id, data):
        url = f"https://api.play.ai/v1/agents/{agent_id}"
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to update agent: {await response.text()}")

    async def save_game_state(self):
        try:
            with open(self.file_path, 'w') as file:
                json.dump(self.game_state, file)
            logger.info("Game state saved successfully")
        except Exception as e:
            logger.error(f"Error saving game state: {e}")

    async def periodic_save(self):
        while True:
            await asyncio.sleep(300)  # Save every 5 minutes
            await self.save_game_state()

    def clean_old_knowledge(self, max_age_days=30):
        current_time = datetime.now()
        old_entries = [key for key, value in self.knowledge_base.items() 
                       if (current_time - value.get('timestamp', current_time)).days > max_age_days]
        for key in old_entries:
            del self.knowledge_base[key]
        logger.info(f"Cleaned {len(old_entries)} old knowledge entries")

    async def scheduled_sync(self):
        try:
            save_task = asyncio.create_task(self.periodic_save())
            while True:
                # 🔄 Fetch recent conversations from play.ai
                conversations = await fetch_recent_conversations()
                for conv in conversations:
                    # 📜 Retrieve the transcript for each conversation
                    transcript = await fetch_conversation_transcript(conv['id'])
                    if transcript:
                        # 💾 Store the transcript in the database
                        await self.store_transcript(conv['id'], transcript)
                
                # 🕐 Wait for 5 minutes before the next sync
                await asyncio.sleep(300)
                self.clean_old_knowledge()
        except asyncio.CancelledError:
            # 🛑 Handle cancellation of the sync task
            logger.info("Scheduled sync task was cancelled.")
        except Exception as e:
            # ❗ Log any unexpected errors
            logger.error(f"An unexpected error occurred in scheduled_sync: {e}")
        finally:
            save_task.cancel()
            await save_task

    async def store_transcript(self, conversation_id, transcript):
        async with session_scope() as session:
            for message in transcript:
                # 📝 Create a new ConversationMessage object for each message in the transcript
                new_message = ConversationMessage(
                    conversation_id=conversation_id,
                    role=message['role'],
                    content=message['content'],
                    timestamp=datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
                )
                # ➕ Add the new message to the database session
                session.add(new_message)
            # ✅ Commit all new messages to the database
            await session.commit()

    # 🔮 Future enhancement: Implement vector database synchronization
    # TODO: Add logic to sync with a vector database for improved search and retrieval

def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    for task in asyncio.all_tasks():
        task.cancel()  # Cancel pending tasks
    asyncio.get_event_loop().stop()  # Stop the event loop