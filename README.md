# Aqua Prime 
_Aqua Prime_ is an integrated bot suite designed to enhance online community interactions on platforms such as Discord and Twitch. By leveraging machine learning, natural language processing, and API integrations, Aqua Prime aims to deliver a rich interactive experience to users.💧

![Aqua Prime](https://i.imgur.com/ba0mt4G.png)
## 🌟 Features 

### Discord Bot
   - 🤖 **Chat with AI**: Engage in conversations with a context-aware AI.
   - 📜 **Summary Fetching**: Effortlessly fetch summaries of recent interactions or specific queries.
   - 🌟 **Reputation System**: Check your reputation based on engagement and sentiment.

### Twitch Bot
   - 🗨️ **Chat Command Handling**: Responds to chat commands and interacts with users.
   - ⚙️ **Interaction Context**: Maintains context for coherent responses.

### Core Components

- **API Client**:
  - Seamless integration with external services.
  - Fetches conversation details and transcripts.
- **Database Integration**:
  - Efficient session management with SQLAlchemy.
  - Data storage for conversations, messages, and user engagement.
- **Natural Language Processing**:
  - AI responses generated using OpenAI's GPT-3.5-turbo.
  - Sentiment analysis for tracking engagement quality.

## 🚀 Getting Started

### Prerequisites
Ensure you have all required environment variables set:
- `DISCORD_TOKEN`: Token for Discord bot.
- `DISCORD_GUILD_ID`: ID of the Discord guild.
- `TWITCH_IRC_TOKEN`: Token for Twitch bot.
- `TWITCH_CLIENT_ID`: Client ID for Twitch API.
- `TWITCH_CHANNEL`: Channel to connect to on Twitch.
- `TWITCH_NICK`: Nickname for the Twitch bot.
- `OPENAI_API_KEY`: API key for OpenAI.
- `PLAY_AI_API_KEY`: API key for Play AI.
- `PLAY_AI_USER_ID`: User ID for Play AI.
- `AGENT_ID`: ID of the agent for Play AI.
- `PLAY_AI_API_URL`: Base URL for Play AI API.

### Running the Bots
#### Discord Bot:
Aqua Prime Bot Suite
Aqua Prime is an integrated bot suite designed to enhance online community interactions on platforms such as Discord and Twitch. By leveraging machine learning, natural language processing, and API integrations, Aqua Prime aims to deliver a rich interactive experience to users.💧
!Aqua Prime
🌟 Features
Discord Bot
🤖 Chat with AI: Engage in conversations with a context-aware AI.
📜 Summary Fetching: Effortlessly fetch summaries of recent interactions or specific queries.
🌟 Reputation System: Check your reputation based on engagement and sentiment.
Twitch Bot
🗨️ Chat Command Handling: Responds to chat commands and interacts with users.
⚙️ Interaction Context: Maintains context for coherent responses.
🚀 Getting Started
Prerequisites
Ensure you have all required environment variables set in a .env file:
Installation
Clone the repository:
Install dependencies:
Running the Bots
To start both Discord and Twitch bots:
📚 Usage
Discord Commands
Use the following commands in Discord:
/chat [message]: Chat with the AI.
/faction_info: Get information about your faction.
/help: Display available commands.
Twitch Commands
In Twitch chat, use these commands:
!chat [message]: Interact with the AI.
!info: Get game information.
!help: Display available commands.
🤖 AI Interaction
The AI, powered by OpenAI's GPT-3.5-turbo, maintains context for each user across platforms. It can engage in conversations, provide game-related information, and assist with various tasks.
🔄 Syncing and Updates
The bot automatically syncs game state and can push updates to the repository. This ensures that the latest game information is always available.
🛠 Troubleshooting
If you encounter any issues:
Check that all environment variables are correctly set.
Ensure you have the latest version of the bot.
Check the logs for any error messages.
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgements
OpenAI for providing the GPT-3.5-turbo model
Discord.py and Twitch-Python for their APIs
For more information, please refer to the documentation in the AquaPrimeKB folder.