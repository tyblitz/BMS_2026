import pytest
import io
from decimal import Decimal
from fastapi.testclient import TestClient
from python_calamine import load_workbook
from app.main import app
from app.core.database import db_manager
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def seed_phase12_data():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.query(User).filter(User.username != "admin").delete()

        admin = session.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("Admin123!"),
                role="admin",
                created_by="system",
            )
            session.add(admin)

        ro = User(
            username="ro_e2e_ncr",
            hashed_password=get_password_hash("Password123!"),
            role="region",
            region="National Capital Region (NCR)",
            created_by="system",
        )
        sdo = User(
            username="sdo_e2e_caloocan",
            hashed_password=get_password_hash("Password123!"),
            role="sdo",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="system",
        )
        school = User(
            username="sch_e2e_amparo",
            hashed_password=get_password_hash("Password123!"),
            role="school",
            school_name="Amparo High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            created_by="system",
        )
        session.add_all([ro, sdo, school])

        # Record for Amparo High School
        r = BMSRecord(
            row_hash="phase12_e2e_hash",
            region="National Capital Region (NCR)",
            division="Division of Caloocan",
            operating_unit="Amparo High School",
            appropriations=Decimal("100000.00"),
            allotment=Decimal("100000.00"),
            obligations_incurred=Decimal("60000.00"),
            disbursement=Decimal("40000.00"),
            created_by="seed",
        )
        session.add(r)
        session.commit()
    finally:
        session.close()


def test_e2e_rbac_security_matrix():
    seed_phase12_data()

    # 1. School Token
    school_tok = create_access_token({"sub": "sch_e2e_amparo", "role": "school", "school_name": "Amparo High School", "division": "Division of Caloocan"})
    h_school = {"Authorization": f"Bearer {school_tok}"}

    # School CAN access school summary
    assert client.get("/api/v1/analytics/school-summary", headers=h_school).status_code == 200
    # School CANNOT access division, region, admin summary
    assert client.get("/api/v1/analytics/division-summary", headers=h_school).status_code == 403
    assert client.get("/api/v1/analytics/region-summary", headers=h_school).status_code == 403
    assert client.get("/api/v1/analytics/admin-summary", headers=h_school).status_code == 403

    # 2. SDO Token
    sdo_tok = create_access_token({"sub": "sdo_e2e_caloocan", "role": "sdo", "division": "Division of Caloocan"})
    h_sdo = {"Authorization": f"Bearer {sdo_tok}"}

    # SDO CAN access division summary
    assert client.get("/api/v1/analytics/division-summary", headers=h_sdo).status_code == 200
    # SDO CANNOT access region or admin summary
    assert client.get("/api/v1/analytics/region-summary", headers=h_sdo).status_code == 403
    assert client.get("/api/v1/analytics/admin-summary", headers=h_sdo).status_code == 403

    # 3. Regional Token
    ro_tok = create_access_token({"sub": "ro_e2e_ncr", "role": "region", "region": "National Capital Region (NCR)"})
    h_ro = {"Authorization": f"Bearer {ro_tok}"}

    # Region CAN access regional & division summary
    assert client.get("/api/v1/analytics/region-summary", headers=h_ro).status_code == 200
    assert client.get("/api/v1/analytics/division-summary?division_name=Division of Caloocan", headers=h_ro).status_code == 200
    # Region CANNOT access admin summary
    assert client.get("/api/v1/analytics/admin-summary", headers=h_ro).status_code == 403

    # 4. Admin Token
    admin_tok = create_access_token({"sub": "admin", "role": "admin"})
    h_admin = {"Authorization": f"Bearer {admin_tok}"}

    # Admin CAN access all endpoints
    assert client.get("/api/v1/analytics/school-summary?school_name=Amparo High School", headers=h_admin).status_code == 200
    assert client.get("/api/v1/analytics/division-summary?division_name=Division of Caloocan", headers=h_admin).status_code == 200
    assert client.get("/api/v1/analytics/region-summary", headers=h_admin).status_code == 200
    assert client.get("/api/v1/analytics/admin-summary", headers=h_admin).status_code == 200


def test_ms_access_export_integrity():
    seed_phase12_data()

    admin_tok = create_access_token({"sub": "admin", "role": "admin"})
    resp = client.get("/api/v1/export", headers={"Authorization": f"Bearer {admin_tok}"})
    assert resp.status_code == 200

    # Read with calamine
    wb = load_workbook(io.BytesIO(resp.content))
    assert "Combine Sheet" in wb.sheet_names
    sheet = wb.get_sheet_by_name("Combine Sheet")
    rows = list(sheet.to_python())

    # Exactly 33 columns
    assert len(rows[0]) == 33
    headers = [str(c).strip() for c in rows[0]]
    assert "TOTAL ADJUSTED APPRO" in headers
    assert "TOTAL ADJUSTED ALLOTMENT" in headers
    assert "UNOBLIGATED" in headers
    assert "UNPAID" in headers
    assert "UNRELEASED" in headers

