"""
Database configuration.

This module initializes the SQLAlchemy engine, session factory,
and declarative base for the application.
"""

from collections.abc import Generator

# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """
    pass


# ==========================
# Database Engine
# ==========================

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # Print SQL queries in debug mode
    pool_pre_ping=True,           # Checks connections before using them
)


# ==========================
# Session Factory
# ==========================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ==========================
# Database Dependency
# ==========================

def get_db() -> Generator[Session, None, None]:
    """
    Yields a database session.

    Used as a FastAPI dependency.

    Example:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==========================
# Utility
# ==========================

def create_tables() -> None:
    """
    Create all database tables.
    """
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)