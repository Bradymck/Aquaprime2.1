import json
import aiohttp
import asyncio

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

    def save_game_state(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.game_state, file)

    async def scheduled_sync(self):
        try:
            while True:
                # Your asynchronous task here
                await some_async_task()  # Example task
                await asyncio.sleep(300)  # Sleep to prevent tight loops
        except asyncio.CancelledError:
            logger.info("Scheduled sync task was cancelled.")
            # No need for break here, just exit the loop
        except Exception as e:
            logger.error(f"An unexpected error occurred in scheduled_sync: {e}")

def signal_handler():
    logger.info("Received shutdown signal. Closing bots...")
    for task in asyncio.all_tasks():
        task.cancel()  # Cancel pending tasks
    asyncio.get_event_loop().stop()  # Stop the event loop

async def main():
    try:
        await asyncio.gather(discord_task, twitch_task, scheduled_sync())
    except asyncio.CancelledError:
        logger.info("Main task was cancelled.")
    finally:
        # Ensure all tasks are completed before exiting
        for task in asyncio.all_tasks():
            task.cancel()
        await asyncio.gather(*asyncio.all_tasks(), return_exceptions=True)

# Example usage
if __name__ == "__main__":
    manager = GameStateManager("./AquaPrimeLORE", "./AquaPrimeLORE/game_state.json")
    print(manager.game_state)