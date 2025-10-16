import os
import datetime as dt
from contextlib import contextmanager
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, Index
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./overtalkerr.db")

# SQLAlchemy 2.0 engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base"""
    pass


class SessionState(Base):
    __tablename__ = "session_state"

    id = Column(Integer, primary_key=True, index=True)
    # Alexa user id or device id as a grouping key
    user_id = Column(String(256), index=True, nullable=False)
    # Request id or a logical conversation id
    conversation_id = Column(String(256), index=True, nullable=False)
    # JSON payload string storing search results and cursor
    state_json = Column(Text, nullable=False)
    # Timestamp for automatic cleanup
    created_at = Column(DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    __table_args__ = (
        # Composite index for faster lookups
        Index('ix_session_user_conv', 'user_id', 'conversation_id'),
        Index('ix_session_created', 'created_at'),
    )


# Create tables
Base.metadata.create_all(bind=engine)


@contextmanager
def db_session():
    """Context manager for database sessions with automatic commit/rollback"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def cleanup_old_sessions(hours: int = 24) -> int:
    """
    Delete conversation states older than specified hours.

    Args:
        hours: Age threshold in hours (default: 24)

    Returns:
        Number of deleted records
    """
    cutoff = dt.datetime.utcnow() - dt.timedelta(hours=hours)
    with db_session() as s:
        deleted = s.query(SessionState).filter(SessionState.created_at < cutoff).delete()
        return deleted
