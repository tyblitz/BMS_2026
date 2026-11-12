import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db_manager
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def seed_phase10_data():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.query(User).filter(User.username != "admin").delete()

        ro_user = User(
            username="ro_test_ncr",
            hashed_password=get_password_hash("Password123!"),
            role="region",
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
        session.add_all([ro_user, sdo_user])
        session.commit()

        # Division 1: Caloocan (100k allot, 90k obli = 90% utilization)
        r1 = BMSRecord(
            row_hash="phase10_h1",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Amparo High School",
            appropriations=Decimal("100000.00"),
            allotment=Decimal("100000.00"),
            obligations_incurred=Decimal("90000.00"),
            disbursement=Decimal("80000.00"),
            particulars="Caloocan Expenses",
            created_by="seed",
        )
        # Division 2: Manila (200k allot, 100k obli = 50% utilization)
        r2 = BMSRecord(
            row_hash="phase10_h2",
            region="National Capital Region (NCR)",
            division="Division of Manila",
            operating_unit="Manila High School",
            appropriations=Decimal("200000.00"),
            allotment=Decimal("200000.00"),
            obligations_incurred=Decimal("100000.00"),
            disbursement=Decimal("70000.00"),
            particulars="Manila Expenses",
            created_by="seed",
        )
        session.add_all([r1, r2])
        session.commit()
    finally:
        session.close()


def test_region_summary_macro_analytics():
    seed_phase10_data()

    ro_token = create_access_token({
        "sub": "ro_test_ncr",
        "role": "region",
        "region": "National Capital Region (NCR)",
    })

    resp = client.get(
        "/api/v1/analytics/region-summary",
        headers={"Authorization": f"Bearer {ro_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["region"] == "National Capital Region (NCR)"
    assert data["total_records"] == 2
    assert data["total_divisions"] == 2
    assert data["total_schools"] == 2

    # Regional Allotment = 100k + 200k = 300k
    assert data["total_adjusted_allotment"] == 300000.00
    # Obligations = 90k + 100k = 190k
    assert data["total_obligations"] == 190000.00
    # Disbursements = 80k + 70k = 150k
    assert data["total_disbursements"] == 150000.00
    # Unobligated = 300k - 190k = 110k
    assert data["unobligated_balance"] == 110000.00
    # Unpaid = 190k - 150k = 40k
    assert data["unpaid_balance"] == 40000.00

    # Leaderboard ordering: Caloocan (90%) should be 1st, Manila (50%) 2nd
    divs = data["divisions_matrix"]
    assert len(divs) == 2
    assert divs[0]["division"] == "Division of Caloocan"
    assert divs[0]["utilization_rate"] == 90.0
    assert divs[1]["division"] == "Division of Manila"
    assert divs[1]["utilization_rate"] == 50.0


def test_region_summary_forbidden_for_sdo():
    seed_phase10_data()

    sdo_token = create_access_token({
        "sub": "sdo_test_caloocan",
        "role": "sdo",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)",
    })

    resp = client.get(
        "/api/v1/analytics/region-summary",
        headers={"Authorization": f"Bearer {sdo_token}"},
    )
    assert resp.status_code == 403
