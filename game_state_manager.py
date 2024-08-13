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
                content = file.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {self.file_path}")
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
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as file:
                json.dump(self.game_state, file)
            logger.info("Game state saved successfully")
        except Exception as e:
            logger.error(f"Error saving game state: {e}")

    async def scheduled_sync(self):
        try:
            while True:
                await self.save_game_state()
                await asyncio.sleep(300)  # Run every 5 minutes
        except asyncio.CancelledError:
            logger.info("Scheduled sync task was cancelled.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in scheduled_sync: {e}")

    def update_agent_knowledge(self, user_id, data):
        if user_id not in self.knowledge_base:
            self.knowledge_base[user_id] = []
        self.knowledge_base[user_id].append(data)

    def get_faction_info(self, user_id):
        # Implement faction info retrieval logic here
        return "Faction info placeholder"

    def get_game_status(self):
        # Implement game status retrieval logic here
        return "Game status placeholder"

    def clean_old_knowledge(self, max_age_days=30):
        current_time = datetime.now()
        old_entries = [key for key, value in self.knowledge_base.items() 
                       if (current_time - value.get('timestamp', current_time)).days > max_age_days]
        for key in old_entries:
            del self.knowledge_base[key]
        logger.info(f"Cleaned {len(old_entries)} old knowledge entries")