import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.base import Base


class DatabaseManager:
    """
    Manages SQLAlchemy engine and sessions dynamically.
    Allows hot-swapping connection strings (SQLite -> MySQL -> Postgres) at runtime
    without restarting the application.
    """
    def __init__(self):
        self.active_url = settings.load_active_database_url()
        self.engine = self._create_engine_for_url(self.active_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _create_engine_for_url(self, url: str):
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        return create_engine(url, connect_args=connect_args, pool_pre_ping=True)

    def get_session(self) -> Generator[Session, None, None]:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_connection(self, url: str) -> tuple[bool, str]:
        """Tests if a candidate database connection URL is reachable."""
        try:
            temp_engine = self._create_engine_for_url(url)
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connection successful."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def switch_database(self, new_url: str) -> tuple[bool, str]:
        """Switches active database to new URL, creates tables, and persists setting."""
        success, msg = self.test_connection(new_url)
        if not success:
            return False, msg

        try:
            new_engine = self._create_engine_for_url(new_url)
            # Create all tables on new database
            Base.metadata.create_all(bind=new_engine)
            
            # Hot swap engine and sessionmaker
            self.engine.dispose()
            self.engine = new_engine
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.active_url = new_url
            
            # Persist setting
            settings.save_active_database_url(new_url)
            return True, f"Successfully switched database to {new_url.split('@')[-1] if '@' in new_url else new_url}"
        except Exception as e:
            return False, f"Failed to switch database: {str(e)}"

    def init_db(self):
        """Initializes tables on the active database."""
        Base.metadata.create_all(bind=self.engine)


db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    yield from db_manager.get_session()

