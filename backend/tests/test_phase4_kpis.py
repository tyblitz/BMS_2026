import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.core.database import db_manager
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def test_records_summary_and_kpis():
    session = next(db_manager.get_session())
    try:
        # Seed test school user if not exists
        school_user = session.query(User).filter(User.username == "school_caloocan_hs").first()
        if not school_user:
            school_user = User(
                username="school_caloocan_hs",
                hashed_password=get_password_hash("Password123!"),
                role="school",
                school_name="Caloocan High School",
                division="Division of Caloocan",
                region="National Capital Region (NCR)",
                created_by="system"
            )
            session.add(school_user)

        # Seed two distinct records
        rec1 = BMSRecord(
            row_hash="kpi_hash_1",
            operating_unit="Caloocan High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            ppa_code="PPA350",
            ppa_control="PPA350 - Junior High School",
            appropriations=Decimal("100000.00"),
            appro_adjust=Decimal("10000.00"),
            allotment=Decimal("100000.00"),
            realignment=Decimal("5000.00"),
            transfer_from=Decimal("2000.00"),
            transfer_to=Decimal("1000.00"),
            obligations_incurred=Decimal("60000.00"),
            disbursement=Decimal("40000.00"),
            created_by="admin",
            is_deleted=False
        )
        rec2 = BMSRecord(
            row_hash="kpi_hash_2",
            operating_unit="Manila Science High School",
            division="Division of Manila",
            region="National Capital Region (NCR)",
            ppa_code="PPA350",
            ppa_control="PPA350 - Junior High School",
            appropriations=Decimal("50000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("50000.00"),
            realignment=Decimal("0.00"),
            transfer_from=Decimal("0.00"),
            transfer_to=Decimal("0.00"),
            obligations_incurred=Decimal("30000.00"),
            disbursement=Decimal("20000.00"),
            created_by="admin",
            is_deleted=False
        )
        session.add(rec1)
        session.add(rec2)
        session.commit()
    finally:
        session.close()

    # 1. Test Admin Records Summary (sees all records)
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    admin_resp = client.get(
        "/api/v1/analytics/records-summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_resp.status_code == 200
    admin_data = admin_resp.json()
    assert admin_data["record_count"] >= 2
    # Check formula: total_unobligated == total_allotment - total_obligations
    expected_unobli = round(admin_data["total_allotment"] - admin_data["total_obligations"], 2)
    assert round(admin_data["total_unobligated"], 2) == expected_unobli
    # Check formula: total_unpaid == total_obligations - total_disbursements
    expected_unpaid = round(admin_data["total_obligations"] - admin_data["total_disbursements"], 2)
    assert round(admin_data["total_unpaid"], 2) == expected_unpaid

    # 2. Test School Records Summary (only sees Caloocan High School)
    school_token = create_access_token({
        "sub": "school_caloocan_hs",
        "role": "school",
        "school_name": "Caloocan High School",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)"
    })
    school_resp = client.get(
        "/api/v1/analytics/records-summary",
        headers={"Authorization": f"Bearer {school_token}"}
    )
    assert school_resp.status_code == 200
    school_data = school_resp.json()
    # Caloocan record: total_adj_allot = 100000 + 5000 + 2000 - 1000 = 106000
    assert school_data["total_allotment"] == 106000.0
    assert school_data["total_obligations"] == 60000.0
    assert school_data["total_disbursements"] == 40000.0
    assert school_data["total_unobligated"] == 46000.0
    assert school_data["total_unpaid"] == 20000.0


def test_users_pagination_and_management():
    session = next(db_manager.get_session())
    try:
        # Seed 5 dummy users to test pagination
        for i in range(5):
            u_name = f"test_user_page_{i}"
            if not session.query(User).filter(User.username == u_name).first():
                session.add(User(
                    username=u_name,
                    hashed_password=get_password_hash("Pass123!"),
                    role="school",
                    school_name=f"School {i}",
                    division="Division of Caloocan",
                    region="National Capital Region (NCR)",
                    created_by="admin"
                ))
        session.commit()
    finally:
        session.close()

    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Query with skip=0, limit=3
    resp_page1 = client.get("/api/v1/users?skip=0&limit=3", headers=headers)
    assert resp_page1.status_code == 200
    data_page1 = resp_page1.json()
    assert len(data_page1["items"]) == 3
    assert data_page1["total"] >= 6
    assert data_page1["skip"] == 0
    assert data_page1["limit"] == 3

    # Query with search
    search_resp = client.get("/api/v1/users?search=test_user_page_2", headers=headers)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert len(search_data["items"]) == 1
    assert search_data["items"][0]["username"] == "test_user_page_2"
