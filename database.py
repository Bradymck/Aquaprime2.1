import logging
from sqlalchemy import Column, DateTime, Float, Integer, String, JSON, ForeignKey, func, Boolean, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import random
import os


# Initialize colorama
init(autoreset=True)

# Aqua Prime themed emojis and symbols
AQUA_EMOJIS = ["🌊", "💧", "🐠", "🐳", "🦈", "🐙", "🦀", "🐚", "🏊‍♂️", "🏄‍♂️", "🤿", "🚤"]

class AquaPrimeFormatter(logging.Formatter):
    def format(self, record):
        aqua_colors = [Fore.CYAN, Fore.BLUE, Fore.GREEN]
        color = random.choice(aqua_colors)
        emoji = random.choice(AQUA_EMOJIS)

        log_message = super().format(record)
        return f"{color}{Style.BRIGHT}{emoji} {log_message}{Style.RESET_ALL}"

logger = logging.getLogger('database')
handler = logging.StreamHandler()
handler.setFormatter(AquaPrimeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///your_database.db', echo=True)
AsyncSessionMaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def session_scope():
    session = AsyncSessionMaker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await add_is_user_column()
    logger.info("Database initialized")

async def add_is_user_column():
    async with engine.begin() as conn:
        # Check if the column exists
        result = await conn.execute(text("PRAGMA table_info(messages)"))
        columns = result.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'is_user' not in column_names:
            # Add the column if it doesn't exist
            await conn.execute(text("ALTER TABLE messages ADD COLUMN is_user BOOLEAN"))
            logger.info("Added 'is_user' column to messages table")
        else:
            logger.info("'is_user' column already exists in messages table")

async def cleanup_old_messages(days=30):
    async with session_scope() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        await session.execute(
            delete(Message).where(Message.timestamp < cutoff_date)
        )
        await session.commit()

async def optimize_database():
    async with session_scope() as session:
        await session.execute("VACUUM")
        await session.execute("ANALYZE")

async def scheduled_database_maintenance():
    while True:
        await asyncio.sleep(86400)  # Run daily
        await cleanup_old_messages()
        await optimize_database()

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    platform = Column(String)
    user_id = Column(String)
    username = Column(String)
    sentiment = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_user = Column(Boolean, default=True)


class UserEngagement(Base):
    __tablename__ = 'user_engagement'
    user_id = Column(String, primary_key=True)
    username = Column(String)
    message_count = Column(Integer, default=0)
    reputation = Column(Integer, default=0)
    overall_sentiment = Column(Float, default=0.0)
    last_active = Column(DateTime, default=datetime.utcnow)

class TranscriptSummary(Base):
    __tablename__ = 'transcript_summaries'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentMemory(Base):
    __tablename__ = 'agent_memories'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, unique=True)
    critical_knowledge = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)

class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, ForeignKey('conversations.conversation_id'))
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime)
    conversation = relationship("Conversation", back_populates="messages")

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, unique=True)
    agent_id = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    summary = Column(String)
    messages = relationship("ConversationMessage", order_by="ConversationMessage.timestamp", back_populates="conversation")

logger.info("Aqua Prime Database Initialized")