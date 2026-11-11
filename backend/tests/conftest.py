import os
import pytest
from pathlib import Path
from sqlalchemy.orm import sessionmaker

TEST_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "bms_test.db"

from app.core.database import db_manager, Base
from app.core.security import get_password_hash
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-wide fixture to isolate tests to bms_test.db."""
    original_url = db_manager.active_url
    original_engine = db_manager.engine
    original_session = db_manager.SessionLocal

    test_url = f"sqlite:///{TEST_DB_PATH.as_posix()}"
    db_manager.active_url = test_url
    db_manager.engine = db_manager._create_engine_for_url(test_url)
    db_manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_manager.engine)

    Base.metadata.drop_all(bind=db_manager.engine)
    Base.metadata.create_all(bind=db_manager.engine)

    # Seed default admin in test DB
    session = next(db_manager.get_session())
    try:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("Admin123!"),
            role="admin",
            created_by="system",
        )
        session.add(admin)
        session.commit()
    finally:
        session.close()

    yield

    # Clean up test database file when done
    try:
        db_manager.engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except Exception:
        pass

    # Restore original database pointers
    db_manager.active_url = original_url
    db_manager.engine = original_engine
    db_manager.SessionLocal = original_session
