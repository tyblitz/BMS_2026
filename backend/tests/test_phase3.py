import io
from pathlib import Path
from fastapi.testclient import TestClient
from python_calamine import load_workbook
from app.main import app
from app.core.database import db_manager
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.bms_record import BMSRecord
from app.services.excel_ingestion import ExcelIngestionService

client = TestClient(app)
FIXTURE_PATH = Path("backend/tests/fixtures/sample_tempTable.xlsx")


def setup_test_users_and_data():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.query(User).filter(User.username != "admin").delete()

        # Seed specific scoped users
        users = [
            User(
                username="school_amparo",
                hashed_password=get_password_hash("Password123!"),
                role="school",
                school_name="Amparo High School",
                division="Division of Caloocan",
                region="National Capital Region (NCR)",
                created_by="test"
            ),
            User(
                username="school_other",
                hashed_password=get_password_hash("Password123!"),
                role="school",
                school_name="Other Secondary School",
                division="Division of Caloocan",
                region="National Capital Region (NCR)",
                created_by="test"
            ),
            User(
                username="sdo_officer",
                hashed_password=get_password_hash("Password123!"),
                role="sdo",
                division="Division of Caloocan",
                region="National Capital Region (NCR)",
                created_by="test"
            ),
            User(
                username="ro_officer",
                hashed_password=get_password_hash("Password123!"),
                role="region",
                region="National Capital Region (NCR)",
                created_by="test"
            ),
        ]
        session.add_all(users)
        session.commit()

        # Ingest 50 sample records (all in Caloocan, Amparo High School in sample)
        ExcelIngestionService.ingest_records(
            file_path_or_bytes=str(FIXTURE_PATH),
            db=session,
            uploaded_by="seed_test"
        )
    finally:
        session.close()


def get_token(username: str, role: str, school_name: str = None, division: str = None, region: str = None):
    return create_access_token({
        "sub": username,
        "role": role,
        "school_name": school_name,
        "division": division,
        "region": region
    })


def test_auth_login():
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Admin123!"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" == "access_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_rbac_scoping():
    setup_test_users_and_data()

    # 1. School User (Amparo High School)
    token_amparo = get_token("school_amparo", "school", school_name="Amparo High School", division="Division of Caloocan", region="National Capital Region (NCR)")
    resp_amparo = client.get("/api/v1/records", headers={"Authorization": f"Bearer {token_amparo}"})
    assert resp_amparo.status_code == 200
    data_amparo = resp_amparo.json()
    assert data_amparo["total"] > 0
    # Every item must belong to Amparo High School
    for item in data_amparo["items"]:
        assert item["operating_unit"] == "Amparo High School"

    # 2. School User with 0 records (Other Secondary School)
    token_other = get_token("school_other", "school", school_name="Other Secondary School", division="Division of Caloocan", region="National Capital Region (NCR)")
    resp_other = client.get("/api/v1/records", headers={"Authorization": f"Bearer {token_other}"})
    assert resp_other.status_code == 200
    assert resp_other.json()["total"] == 0

    # 3. SDO User (Division of Caloocan)
    token_sdo = get_token("sdo_officer", "sdo", division="Division of Caloocan", region="National Capital Region (NCR)")
    resp_sdo = client.get("/api/v1/records", headers={"Authorization": f"Bearer {token_sdo}"})
    assert resp_sdo.status_code == 200
    assert resp_sdo.json()["total"] == 50

    # 4. Regional User (National Capital Region)
    token_ro = get_token("ro_officer", "region", region="National Capital Region (NCR)")
    resp_ro = client.get("/api/v1/records", headers={"Authorization": f"Bearer {token_ro}"})
    assert resp_ro.status_code == 200
    assert resp_ro.json()["total"] == 50


def test_crud_lifecycle_and_soft_delete():
    setup_test_users_and_data()
    token_amparo = get_token("school_amparo", "school", school_name="Amparo High School", division="Division of Caloocan", region="National Capital Region (NCR)")
    headers = {"Authorization": f"Bearer {token_amparo}"}

    # 1. Create Record
    new_rec = {
        "ppa_control": "PPA999 - General Management",
        "appropriation_type": "Regular",
        "allotment_period": "Current",
        "allotment_class": "MOOE",
        "date_bms": "46050",
        "account_code": "5020101000",
        "obligations_incurred": 10000.0,
        "disbursement": 6000.0,
        "appropriations": 50000.0,
        "allotment": 40000.0,
        "transfer_to": 0.0,
        "transfer_from": 0.0,
        "particulars": "Office Supplies Procurement Test",
        "uacs_pap_code": "310400100003000",
        "dv_amount": 6000.0,
        "region": "National Capital Region (NCR)",
        "division": "Division of Caloocan",
        "operating_unit": "Amparo High School",
        "org_code_uacs": "070010913001",
        "appro_adjust": 0.0,
        "realignment": 0.0,
        "fund_source": "101101",
        "locality": "School",
        "legal_basis": "GAA 2026",
        "rc": "SCH-IU",
        "reg": "NA",
        "ccet_code": "NA",
        "ledger": "NA"
    }

    create_resp = client.post("/api/v1/records", json=new_rec, headers=headers)
    assert create_resp.status_code == 201
    created_item = create_resp.json()
    record_id = created_item["id"]
    assert created_item["created_by"] == "school_amparo"
    # Dynamic calculations check
    assert float(created_item["total_adjusted_appro"]) == 50000.0
    assert float(created_item["total_adjusted_allotment"]) == 40000.0
    assert float(created_item["unobligated"]) == 30000.0 # 40,000 - 10,000
    assert float(created_item["unpaid"]) == 4000.0       # 10,000 - 6,000

    # 2. Get Single Record
    get_resp = client.get(f"/api/v1/records/{record_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == record_id

    # 3. Update Record
    update_payload = {"particulars": "Updated Particulars Test", "disbursement": 10000.0}
    put_resp = client.put(f"/api/v1/records/{record_id}", json=update_payload, headers=headers)
    assert put_resp.status_code == 200
    updated_data = put_resp.json()
    assert updated_data["particulars"] == "Updated Particulars Test"
    assert updated_data["edited_by"] == "school_amparo"
    assert float(updated_data["unpaid"]) == 0.0 # 10,000 - 10,000 = 0

    # 4. Soft Delete Record
    del_resp = client.delete(f"/api/v1/records/{record_id}", headers=headers)
    assert del_resp.status_code == 200

    # Record should now be inaccessible via GET
    get_after_del = client.get(f"/api/v1/records/{record_id}", headers=headers)
    assert get_after_del.status_code == 404

    # Verify directly in DB that record is NOT physically deleted, but soft-deleted
    session = next(db_manager.get_session())
    try:
        db_rec = session.query(BMSRecord).filter(BMSRecord.id == record_id).first()
        assert db_rec is not None
        assert db_rec.is_deleted is True
        assert db_rec.deleted_by == "school_amparo"
        assert db_rec.deleted_on is not None
    finally:
        session.close()


def test_upload_and_export_api():
    setup_test_users_and_data()
    token_admin = get_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Test Upload
    with open(FIXTURE_PATH, "rb") as f:
        upload_resp = client.post(
            "/api/v1/upload",
            files={"files": ("sample_tempTable.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=headers
        )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["files_processed"] == 1
    # Since 50 rows were already seeded, they should be reported as duplicates
    assert upload_data["overall_summary"]["total_duplicates_skipped"] == 50

    # Test Export
    export_resp = client.get("/api/v1/export/excel", headers=headers)
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Read exported stream
    wb = load_workbook(io.BytesIO(export_resp.content))
    assert "Combine Sheet" in wb.sheet_names
    sheet = wb.get_sheet_by_name("Combine Sheet")
    rows = list(sheet.to_python())
    assert len(rows[0]) == 33
    assert len(rows) == 51 # 1 header + 50 records


def test_database_settings_api():
    token_admin = get_token("admin", "admin")
    headers = {"Authorization": f"Bearer {token_admin}"}

    # Get active DB info
    info_resp = client.get("/api/v1/settings/db", headers=headers)
    assert info_resp.status_code == 200
    assert "dialect" in info_resp.json()

    # Test connection endpoint
    test_resp = client.post(
        "/api/v1/settings/db/test",
        json={"database_url": "sqlite:///:memory:"},
        headers=headers
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["success"] is True
