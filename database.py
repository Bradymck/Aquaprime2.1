from sqlalchemy import create_engine, Column, DateTime, Float, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///unified_chat_memory.db', poolclass=QueuePool, pool_size=10, max_overflow=20)
SessionMaker = sessionmaker(bind=engine)

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

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, unique=True)
    agent_id = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    summary = Column(String)

class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, ForeignKey('conversations.conversation_id'))
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime)
    conversation = relationship("Conversation", back_populates="messages")

Conversation.messages = relationship("ConversationMessage", order_by=ConversationMessage.timestamp, back_populates="conversation")

@contextmanager
def session_scope():
    session = SessionMaker()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    Base.metadata.create_all(engine)

def get_latest_summary():
    # Implement logic to retrieve the most recent summary from the database
    pass

def get_relevant_summary(query):
    # Implement logic to find a summary relevant to the given query
    pass