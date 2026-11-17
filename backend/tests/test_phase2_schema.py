import json
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.bms_record import BMSRecord
from app.models.record_audit_log import RecordAuditLog
from app.core.database import db_manager

client = TestClient(app)


def test_audit_log_tracking_on_crud():
    """Verify that update, delete, and restore create immutable audit log entries."""
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create a record via API
    payload = {
        "ppa_control": "PPA350 - Operation of Schools - Junior High School (Grade 7 to Grade 10)",
        "operating_unit": "School Audit Test",
        "division": "Division of Caloocan",
        "region": "National Capital Region (NCR)",
        "allotment": "100000.00",
        "obligations_incurred": "50000.00",
        "disbursement": "25000.00",
        "particulars": "Audit trail test line"
    }
    create_resp = client.post("/api/v1/records", json=payload, headers=headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    record_id = created_data["id"]
    assert created_data["ppa_code"] == "PPA350"
    assert "Operation of Schools" in created_data["ppa_description"]

    session = next(db_manager.get_session())
    try:
        # Check CREATE audit log
        create_log = session.query(RecordAuditLog).filter(
            RecordAuditLog.record_id == record_id,
            RecordAuditLog.action == "CREATE"
        ).first()
        assert create_log is not None
        assert create_log.changed_by == "admin"

        # 2. Update record obligations from 50,000 to 75,000
        upd_resp = client.put(
            f"/api/v1/records/{record_id}",
            json={"obligations_incurred": "75000.00"},
            headers=headers
        )
        assert upd_resp.status_code == 200

        # Check UPDATE audit log captures old and new values
        upd_log = session.query(RecordAuditLog).filter(
            RecordAuditLog.record_id == record_id,
            RecordAuditLog.action == "UPDATE"
        ).first()
        assert upd_log is not None
        assert "50000.00" in upd_log.old_values
        assert "75000.00" in upd_log.new_values

        # 3. Delete record
        del_resp = client.delete(f"/api/v1/records/{record_id}", headers=headers)
        assert del_resp.status_code == 200

        del_log = session.query(RecordAuditLog).filter(
            RecordAuditLog.record_id == record_id,
            RecordAuditLog.action == "DELETE"
        ).first()
        assert del_log is not None

        # 4. Restore record
        rest_resp = client.post(f"/api/v1/records/{record_id}/restore", headers=headers)
        assert rest_resp.status_code == 200

        rest_log = session.query(RecordAuditLog).filter(
            RecordAuditLog.record_id == record_id,
            RecordAuditLog.action == "RESTORE"
        ).first()
        assert rest_log is not None
    finally:
        session.close()


def test_row_hash_allows_duplicates_without_integrity_error():
    """Verify that row_hash is no longer strictly unique in database schema."""
    session = next(db_manager.get_session())
    try:
        shared_hash = "shared_duplicate_test_hash_123"
        rec1 = BMSRecord(
            row_hash=shared_hash,
            operating_unit="Station 1",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            appro_adjust=Decimal("-1000.00"),
            created_by="system"
        )
        rec2 = BMSRecord(
            row_hash=shared_hash,
            operating_unit="Station 1",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            appro_adjust=Decimal("-2500.00"),
            created_by="system"
        )
        session.add(rec1)
        session.add(rec2)
        session.commit()

        count = session.query(BMSRecord).filter(BMSRecord.row_hash == shared_hash).count()
        assert count == 2
    finally:
        session.close()
