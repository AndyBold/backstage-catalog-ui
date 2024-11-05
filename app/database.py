#!/usr/bin/env python3

from typing import Generator
from contextlib import contextmanager
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedAsDataclass,
    Session,
    sessionmaker,
    scoped_session,
)
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase, MappedAsDataclass):
    """Base class for all SQLAlchemy models"""

    pass


class DatabaseManager:
    """Database manager for SQLAlchemy operations"""

    def __init__(self, app: Flask = None):
        self.app = app
        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None
        self._scoped_session: scoped_session | None = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the database with the Flask app"""
        self.app = app

        # Create engine with specific configuration
        # TODO: Update this to use values from config.py
        self._engine = create_engine(
            app.config["SQLALCHEMY_DATABASE_URI"],
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=app.debug,
            echo_pool=app.debug,
            logging_name="sqlalchemy.engine",
        )

        # Set up session factory
        self._session_factory = sessionmaker(
            bind=self._engine, expire_on_commit=False, autoflush=False
        )

        # Create scoped session
        self._scoped_session = scoped_session(self._session_factory)

        # Set up SQLite specific pragma statements
        if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
            self._setup_sqlite_engine()

        # Register teardown context
        app.teardown_appcontext(self._teardown)

    def _setup_sqlite_engine(self) -> None:
        """Configure SQLite specific settings"""

        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute(
                "PRAGMA synchronous=NORMAL"
            )  # Faster writes with some safety
            cursor.execute("PRAGMA foreign_keys=ON")  # Enable foreign key support
            cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            cursor.execute("PRAGMA cache_size=-2000")  # Set cache size to 2MB
            cursor.close()

    def _teardown(self, exception=None) -> None:
        """Remove the current session"""
        if self._scoped_session is not None:
            self._scoped_session.remove()

    @property
    def session(self) -> scoped_session:
        """Get the current database session"""
        if self._scoped_session is None:
            raise RuntimeError("DatabaseManager is not initialized with an application")
        return self._scoped_session

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine"""
        if self._engine is None:
            raise RuntimeError("DatabaseManager is not initialized with an application")
        return self._engine

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager for database sessions

        Usage:
            with db_manager.session_scope() as session:
                session.add(some_object)
                session.commit()
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Error in session: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def create_all(self) -> None:
        """Create all database tables"""
        Base.metadata.create_all(self._engine)

    def drop_all(self) -> None:
        """Drop all database tables"""
        Base.metadata.drop_all(self._engine)


# Create database manager instance
db_manager = DatabaseManager()

# Create Flask-SQLAlchemy instance for compatibility
db = SQLAlchemy(model_class=Base)
