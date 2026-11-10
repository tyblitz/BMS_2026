from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.core.database import db_manager
from app.models.user import User
from app.models.bms_record import BMSRecord

client = TestClient(app)


def get_admin_token():
    return create_access_token({"sub": "admin", "role": "admin"})


def test_user_management_crud():
    headers = {"Authorization": f"Bearer {get_admin_token()}"}

    # 1. List Users
    list_resp = client.get("/api/v1/users", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 2. Create User
    new_user = {
        "username": "test_sdo_officer_new",
        "email": "sdo_new@deped.gov.ph",
        "password": "Password123!",
        "role": "sdo",
        "division": "Division of Quezon City",
        "region": "National Capital Region (NCR)",
        "is_active": True
    }
    create_resp = client.post("/api/v1/users", json=new_user, headers=headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    user_id = created_data["id"]
    assert created_data["username"] == "test_sdo_officer_new"
    assert created_data["division"] == "Division of Quezon City"

    # 3. Update User
    update_payload = {"email": "updated_sdo@deped.gov.ph", "division": "Division of Manila"}
    put_resp = client.put(f"/api/v1/users/{user_id}", json=update_payload, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["email"] == "updated_sdo@deped.gov.ph"
    assert put_resp.json()["division"] == "Division of Manila"

    # 4. Soft Delete User
    del_resp = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert del_resp.status_code == 200

    # User should no longer appear in active list
    list_after = client.get("/api/v1/users", headers=headers)
    active_usernames = [u["username"] for u in list_after.json()["items"]]
    assert "test_sdo_officer_new" not in active_usernames

    # 5. Prevent deleting own admin account
    session = next(db_manager.get_session())
    try:
        admin = session.query(User).filter(User.username == "admin").first()
        del_self = client.delete(f"/api/v1/users/{admin.id}", headers=headers)
        assert del_self.status_code == 400
        assert "Cannot delete your own admin account" in del_self.json()["detail"]
    finally:
        session.close()


def test_soft_delete_and_restore_record():
    headers = {"Authorization": f"Bearer {get_admin_token()}"}
    session = next(db_manager.get_session())
    try:
        # Create a test record
        rec = BMSRecord(
            row_hash="test_restore_hash_999",
            region="NCR",
            division="Caloocan",
            operating_unit="Restore Test High School",
            allotment_class="MOOE",
            appropriations=100000.0,
            allotment=100000.0,
            obligations_incurred=50000.0,
            disbursement=20000.0,
            created_by="admin",
            is_deleted=False
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
        rec_id = rec.id

        # 1. Soft-delete via API
        del_resp = client.delete(f"/api/v1/records/{rec_id}", headers=headers)
        assert del_resp.status_code == 200

        # Verify record is soft-deleted
        session.refresh(rec)
        assert rec.is_deleted is True

        # 2. Restore record via API
        restore_resp = client.post(f"/api/v1/records/{rec_id}/restore", headers=headers)
        assert restore_resp.status_code == 200
        restored_data = restore_resp.json()
        assert restored_data["id"] == rec_id
        assert restored_data["is_deleted"] is False

        # Verify record is active in DB again
        session.refresh(rec)
        assert rec.is_deleted is False
        assert rec.deleted_on is None
        assert rec.deleted_by is None

    finally:
        session.close()
