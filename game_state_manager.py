import json
import requests

class GameStateManager:
    def __init__(self, repo_path, file_path):
        self.repo_path = repo_path
        self.file_path = file_path
        self.game_state = self.load_game_state()

    def load_game_state(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def summarize_transcript(self, transcript):
        # Implement your summarization logic here
        summary = "Summary of the transcript"  # Placeholder
        return summary

    def update_agent(self, agent_id, data):
        url = f"https://api.play.ai/v1/agents/{agent_id}"
        response = requests.patch(url, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to update agent: {response.text}")

    def save_game_state(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.game_state, file)

# Example usage
if __name__ == "__main__":
    manager = GameStateManager("./AquaPrimeLORE", "./AquaPrimeLORE/game_state.json")
    print(manager.game_state)
