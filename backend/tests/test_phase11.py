import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def seed_phase11_data():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.query(User).filter(User.username != "admin").delete()

        # Seed 1 admin, 1 ro, 1 sdo, 1 school
        ro_user = User(
            username="ro_admin_test",
            hashed_password=get_password_hash("Password123!"),
            role="region",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        sdo_user = User(
            username="sdo_admin_test",
            hashed_password=get_password_hash("Password123!"),
            role="sdo",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        school_user = User(
            username="sch_admin_test",
            hashed_password=get_password_hash("Password123!"),
            role="school",
            school_name="Amparo High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        session.add_all([ro_user, sdo_user, school_user])

        # Record
        rec = BMSRecord(
            row_hash="phase11_rec1",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Amparo High School",
            appropriations=Decimal("500000.00"),
            allotment=Decimal("500000.00"),
            obligations_incurred=Decimal("300000.00"),
            disbursement=Decimal("200000.00"),
            created_by="seed",
        )
        session.add(rec)
        session.commit()
    finally:
        session.close()


def test_admin_summary_telemetry():
    seed_phase11_data()

    admin_token = create_access_token({
        "sub": "admin",
        "role": "admin",
    })

    resp = client.get(
        "/api/v1/analytics/admin-summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Database
    assert "database" in data
    assert data["database"]["active_records"] == 1
    assert data["database"]["deleted_records"] == 0

    # Users: admin + 1 ro + 1 sdo + 1 school = 4
    assert data["users"]["total"] == 4
    assert data["users"]["admin"] == 1
    assert data["users"]["region"] == 1
    assert data["users"]["sdo"] == 1
    assert data["users"]["school"] == 1

    # Financial
    assert data["financial"]["total_adjusted_allotment"] == 500000.00
    assert data["financial"]["total_obligations"] == 300000.00
    assert data["financial"]["total_disbursements"] == 200000.00
    assert data["financial"]["unobligated_balance"] == 200000.00
    assert data["financial"]["unpaid_balance"] == 100000.00
    assert data["financial"]["utilization_rate"] == 60.0


def test_admin_summary_forbidden_for_non_admin():
    seed_phase11_data()

    school_token = create_access_token({
        "sub": "sch_admin_test",
        "role": "school",
        "school_name": "Amparo High School",
    })

    resp = client.get(
        "/api/v1/analytics/admin-summary",
        headers={"Authorization": f"Bearer {school_token}"},
    )
    assert resp.status_code == 403

