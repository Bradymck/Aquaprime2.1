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
Ensure you have all required environment variables: `DISCORD_TOKEN`, `DISCORD_GUILD_ID`, `TWITCH_IRC_TOKEN`, `TWITCH_CLIENT_ID`, `TWITCH_CHANNEL`, `TWITCH_NICK`, `OPENAI_API_KEY`.

### Running the Bots
#### Discord Bot: