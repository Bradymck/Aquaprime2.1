import os
import discord
import sqlite3
import logging
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def setup_database():
    conn = sqlite3.connect('chat_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    logger.info('Discord Bot: We have logged in as {0.user}'.format(bot))
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

@bot.tree.command(name='logmessage', description='Log a custom message')
async def log_message(interaction: discord.Interaction, message: app_commands.StringOption(description="Enter your message here")):
    conn = sqlite3.connect('chat_memory.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO messages (content) VALUES (?)', (message,))
        conn.commit()
        await interaction.response.send_message(f"Logged message: '{message}'")
    except sqlite3.Error as e:
        logger.error(f"Error saving message to database: {e}")
        await interaction.response.send_message("An error occurred while trying to log your message.")
    finally:
        conn.close()

@bot.command(name='showallmessages')
async def show_all_messages(ctx):
    try:
        conn = sqlite3.connect('chat_memory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, content FROM messages ORDER BY created_at DESC')
        all_messages = cursor.fetchall()
        messages = '\n'.join([f"ID: {msg[0]}, Content: {msg[1]}" for msg in all_messages])
        await ctx.send(f"All Messages in Memory:\n{messages}")
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        await ctx.send("An error occurred while accessing the database.")

if __name__ == "__main__":
    setup_database()
    token = os.getenv("DISCORD_TOKEN") or ""
    if token == "":
        raise Exception("Please add your Discord token to the Secrets pane.")
    bot.run(token)