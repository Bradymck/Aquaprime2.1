import logging
from sqlalchemy import Column, DateTime, Float, Integer, String, JSON, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
from datetime import datetime
import random
import os

# Initialize colorama here if needed
# from colorama import init, Fore, Style
# init(autoreset=True)

# Aqua Prime themed emojis and symbols
# AQUA_EMOJIS = ["🌊", "💧", "🐠", "🐳", "🦈", "🐙", "🦀", "🐚", "🏊‍♂️", "🏄‍♂️", "🤿", "🚤"]

class AquaPrimeFormatter(logging.Formatter):
    def format(self, record):
        log_message = super().format(record)
        return f"{log_message}"  # Removed emojis

logger = logging.getLogger('database')
handler = logging.StreamHandler()
handler.setFormatter(AquaPrimeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///unified_chat_memory.db', echo=True)
AsyncSessionMaker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def session_scope():
    async_session = AsyncSessionMaker()  # Create a new session
    try:
        yield async_session  # Yield the session to the caller
        await async_session.commit()  # Commit changes after exiting the block
    except Exception as e:
        await async_session.rollback()  # Rollback on error
        raise e
    finally:
        await async_session.close()  # Close the session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

# Define your SQLAlchemy models below...
class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    platform = Column(String)
    user_id = Column(String)
    username = Column(String)
    sentiment = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# (Other model definitions...)

logger.info("Aqua Prime Database Initialized")