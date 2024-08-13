import logging
from sqlalchemy import Column, DateTime, Float, Integer, String, JSON, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
from datetime import datetime
import random
import os


Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///unified_chat_memory.db', echo=True)
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
    logger.info("Database initialized")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    platform = Column(String)
    user_id = Column(String)
    username = Column(String)
    sentiment = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)

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

logger = logging.getLogger('database')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("Aqua Prime Database Initialized")