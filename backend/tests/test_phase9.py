import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def seed_phase9_data():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.query(User).filter(User.username != "admin").delete()

        # Users
        sdo_user = User(
            username="sdo_test_caloocan",
            hashed_password=get_password_hash("Password123!"),
            role="sdo",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        school_user = User(
            username="sch_test_amparo",
            hashed_password=get_password_hash("Password123!"),
            role="school",
            school_name="Amparo High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        session.add_all([sdo_user, school_user])
        session.commit()

        # School 1 in Caloocan: Amparo High School
        r1 = BMSRecord(
            row_hash="phase9_h1",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Amparo High School",
            appropriations=Decimal("200000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("200000.00"),
            obligations_incurred=Decimal("150000.00"),
            disbursement=Decimal("100000.00"),
            particulars="Amparo Supplies",
            account_code="5020301000",
            created_by="seed",
        )
        # School 2 in Caloocan: Bagong Silang High School
        r2 = BMSRecord(
            row_hash="phase9_h2",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Bagong Silang High School",
            appropriations=Decimal("300000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("300000.00"),
            obligations_incurred=Decimal("200000.00"),
            disbursement=Decimal("180000.00"),
            particulars="Silang Utilities",
            account_code="5020401000",
            created_by="seed",
        )
        session.add_all([r1, r2])
        session.commit()
    finally:
        session.close()


def test_division_summary_aggregation():
    seed_phase9_data()

    sdo_token = create_access_token({
        "sub": "sdo_test_caloocan",
        "role": "sdo",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)",
    })

    resp = client.get(
        "/api/v1/analytics/division-summary",
        headers={"Authorization": f"Bearer {sdo_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["division"] == "Division of Caloocan"
    assert data["total_records"] == 2
    assert data["total_schools"] == 2

    # Division Totals: 200k + 300k = 500k Allotment
    assert data["total_adjusted_allotment"] == 500000.00
    # Obligations: 150k + 200k = 350k
    assert data["total_obligations"] == 350000.00
    # Disbursements: 100k + 180k = 280k
    assert data["total_disbursements"] == 280000.00
    # Unobligated: 500k - 350k = 150k
    assert data["unobligated_balance"] == 150000.00
    # Unpaid: 350k - 280k = 70k
    assert data["unpaid_balance"] == 70000.00
    # Division % Utilization: 350k / 500k * 100 = 70.0%
    assert data["utilization_rate"] == 70.0

    # Schools matrix
    schools = {s["school_name"]: s for s in data["schools_matrix"]}
    assert "Amparo High School" in schools
    assert "Bagong Silang High School" in schools
    assert schools["Amparo High School"]["utilization_rate"] == 75.0
    assert schools["Bagong Silang High School"]["utilization_rate"] == 66.67


def test_division_summary_forbidden_for_school():
    seed_phase9_data()

    school_token = create_access_token({
        "sub": "sch_test_amparo",
        "role": "school",
        "school_name": "Amparo High School",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)",
    })

    resp = client.get(
        "/api/v1/analytics/division-summary",
        headers={"Authorization": f"Bearer {school_token}"},
    )
    assert resp.status_code == 403

