"""
Initializes the database schema and seeds a default SuperAdmin account.
"""
import sys
from pathlib import Path

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import db_manager
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User
from app.models.bms_record import BMSRecord


def initialize_database():
    print(f"Connecting to database: {db_manager.active_url}")
    # Create all tables
    db_manager.init_db()
    print("✓ All database tables created successfully.")

    # Seed initial SuperAdmin account if not exists
    session = next(db_manager.get_session())
    try:
        admin_user = session.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@deped.gov.ph",
                hashed_password=get_password_hash("Admin123!"),
                role="admin",
                is_active=True,
                created_by="system_init"
            )
            session.add(admin_user)
            session.commit()
            print("✓ Default SuperAdmin account seeded: username='admin', password='Admin123!'")
        else:
            print("✓ Admin account already exists.")
    finally:
        session.close()


if __name__ == "__main__":
    initialize_database()
