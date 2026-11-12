import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def seed_phase8_data():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.query(User).filter(User.username != "admin").delete()

        # Seed 1 school user and records
        school_user = User(
            username="sch_test_amparo",
            hashed_password=get_password_hash("Password123!"),
            role="school",
            school_name="Amparo High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        sdo_user = User(
            username="sdo_test_caloocan",
            hashed_password=get_password_hash("Password123!"),
            role="sdo",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="test",
        )
        session.add_all([school_user, sdo_user])
        session.commit()

        # Seed 2 records for Amparo High School
        r1 = BMSRecord(
            row_hash="phase8_hash_001",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Amparo High School",
            appropriations=Decimal("100000.00"),
            appro_adjust=Decimal("5000.00"),
            allotment=Decimal("90000.00"),
            realignment=Decimal("2000.00"),
            transfer_from=Decimal("1000.00"),
            transfer_to=Decimal("3000.00"),
            obligations_incurred=Decimal("60000.00"),
            disbursement=Decimal("45000.00"),
            particulars="Office Supplies",
            account_code="5020301000",
            created_by="seed",
        )
        r2 = BMSRecord(
            row_hash="phase8_hash_002",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Amparo High School",
            appropriations=Decimal("50000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("40000.00"),
            realignment=Decimal("0.00"),
            transfer_from=Decimal("0.00"),
            transfer_to=Decimal("0.00"),
            obligations_incurred=Decimal("25000.00"),
            disbursement=Decimal("20000.00"),
            particulars="Electricity Expenses",
            account_code="5020401000",
            created_by="seed",
        )
        session.add_all([r1, r2])
        session.commit()
    finally:
        session.close()


def test_school_summary_calculations():
    seed_phase8_data()

    token = create_access_token({
        "sub": "sch_test_amparo",
        "role": "school",
        "school_name": "Amparo High School",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)",
    })

    resp = client.get(
        "/api/v1/analytics/school-summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["school_name"] == "Amparo High School"
    assert data["total_records"] == 2

    # Math verification:
    # Appro: 100k + 5k (r1) + 50k (r2) = 155,000.00
    assert data["total_adjusted_appro"] == 155000.00

    # Allotment: (90k + 2k + 1k - 3k) + 40k = 90,000 + 40,000 = 130,000.00
    assert data["total_adjusted_allotment"] == 130000.00

    # Obligations: 60k + 25k = 85,000.00
    assert data["total_obligations"] == 85000.00

    # Disbursements: 45k + 20k = 65,000.00
    assert data["total_disbursements"] == 65000.00

    # Unobligated: 130k - 85k = 45,000.00
    assert data["unobligated_balance"] == 45000.00

    # Unpaid: 85k - 65k = 20,000.00
    assert data["unpaid_balance"] == 20000.00

    # Utilization rate: 85k / 130k * 100 = 65.38%
    assert data["utilization_rate"] == 65.38

    # Recent records
    assert len(data["recent_records"]) == 2
    assert data["recent_records"][0]["particulars"] in ["Office Supplies", "Electricity Expenses"]


def test_school_summary_sdo_scoping():
    seed_phase8_data()

    # SDO token for Caloocan
    sdo_token = create_access_token({
        "sub": "sdo_test_caloocan",
        "role": "sdo",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)",
    })

    # Allowed: SDO querying a school in Caloocan
    resp_ok = client.get(
        "/api/v1/analytics/school-summary?school_name=Amparo High School",
        headers={"Authorization": f"Bearer {sdo_token}"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["school_name"] == "Amparo High School"

    # Forbidden: SDO querying a school outside their division
    resp_forbidden = client.get(
        "/api/v1/analytics/school-summary?school_name=Manila High School",
        headers={"Authorization": f"Bearer {sdo_token}"},
    )
    assert resp_forbidden.status_code == 403

