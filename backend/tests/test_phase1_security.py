import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.bms_record import BMSRecord
from app.models.user import User
from app.core.database import db_manager

client = TestClient(app)


def test_restore_scope_isolation():
    """Verify that a school user cannot restore another school's deleted record."""
    session = next(db_manager.get_session())
    try:
        # Create user School A
        user_a = User(
            username="test_school_a_user",
            hashed_password="fake",
            role="school",
            school_name="School A",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="admin"
        )
        session.add(user_a)

        # Create a deleted record for School B
        rec = BMSRecord(
            row_hash="test_restore_hash_001",
            operating_unit="School B",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            is_deleted=True,
            created_by="admin"
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        rec_id = rec.id

        # Authenticate as School A
        school_a_token = create_access_token({
            "sub": "test_school_a_user",
            "role": "school",
            "school_name": "School A",
            "division": "Division of Caloocan",
            "region": "National Capital Region (NCR)"
        })

        resp = client.post(
            f"/api/v1/records/{rec_id}/restore",
            headers={"Authorization": f"Bearer {school_a_token}"}
        )
        assert resp.status_code == 404
        assert "Archived record not found or outside authorized scope" in resp.json()["detail"]
    finally:
        session.close()


def test_update_scope_escalation_prevention():
    """Verify that a school user cannot reassign record to another school."""
    session = next(db_manager.get_session())
    try:
        # Create user School A if not exists
        user_a = session.query(User).filter(User.username == "test_school_a_user_upd").first()
        if not user_a:
            user_a = User(
                username="test_school_a_user_upd",
                hashed_password="fake",
                role="school",
                school_name="School A",
                division="Division of Caloocan",
                region="National Capital Region (NCR)",
                created_by="admin"
            )
            session.add(user_a)

        # Create record for School A
        rec = BMSRecord(
            row_hash="test_update_hash_001",
            operating_unit="School A",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            is_deleted=False,
            created_by="test_school_a_user_upd"
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        rec_id = rec.id

        school_a_token = create_access_token({
            "sub": "test_school_a_user_upd",
            "role": "school",
            "school_name": "School A",
            "division": "Division of Caloocan",
            "region": "National Capital Region (NCR)"
        })

        resp = client.put(
            f"/api/v1/records/{rec_id}",
            json={"operating_unit": "School B"},
            headers={"Authorization": f"Bearer {school_a_token}"}
        )
        assert resp.status_code == 403
        assert "cannot change record operating_unit" in resp.json()["detail"]
    finally:
        session.close()


def test_password_max_length_rejection():
    """Verify that passwords exceeding 72 bytes are rejected cleanly without silent truncation."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "A" * 75}
    )
    assert resp.status_code == 400
    assert "Password cannot exceed 72 bytes" in resp.json()["detail"]
