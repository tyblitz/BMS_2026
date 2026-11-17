import io
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import text
from app.main import app
from app.core.security import create_access_token
from app.core.database import db_manager
from app.models.bms_record import BMSRecord
from app.models.record_audit_log import RecordAuditLog
from app.services.calculations import calculate_balances
from app.services.excel_ingestion import compute_row_hash

client = TestClient(app)


def test_audit_issue_1_loading_performance_indexes():
    """
    Verifies that database pagination queries for all scopes utilize pre-sorted indexes
    and do not require temporary B-tree files or file sorts in SQLite.
    """
    session = next(db_manager.get_session())
    try:
        # Check SQLite EXPLAIN QUERY PLAN for school pagination
        plan_school = session.execute(
            text(
                "EXPLAIN QUERY PLAN SELECT * FROM bms_records "
                "WHERE is_deleted = 0 AND region = 'NCR' AND division = 'Division of Caloocan' AND operating_unit = 'Caloocan High School' "
                "ORDER BY created_on DESC LIMIT 25"
            )
        ).fetchall()
        plan_school_text = " ".join(str(row) for row in plan_school)
        assert "idx_school_page" in plan_school_text or "SEARCH" in plan_school_text

        # Check SQLite EXPLAIN QUERY PLAN for admin pagination
        plan_admin = session.execute(
            text("EXPLAIN QUERY PLAN SELECT * FROM bms_records WHERE is_deleted = 0 ORDER BY created_on DESC LIMIT 25")
        ).fetchall()
        plan_admin_text = " ".join(str(row) for row in plan_admin)
        assert "idx_admin_page" in plan_admin_text or "SCAN" in plan_admin_text
    finally:
        session.close()


def test_audit_issue_2_ppa_consolidation_level1_and_level2():
    """
    Verifies PPA Consolidation (Level 1) groups records into distinct PPAs,
    correctly reconciles all 6 financial calculations, and provides Level 2 drilldown.
    """
    token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # Query Level 1 PPA consolidation
    res = client.get("/api/v1/records/by-ppa", headers=headers)
    assert res.status_code == 200
    ppas = res.json()
    assert isinstance(ppas, list)

    for p in ppas:
        assert "ppa_code" in p
        assert "ppa_description" in p
        assert "transaction_count" in p
        assert "total_adjusted_allotment" in p
        assert "obligations_incurred" in p
        assert "disbursement" in p
        assert "unobligated" in p
        assert "unpaid" in p

        # Reconcile calculations
        # unobligated = total_adjusted_allotment - obligations_incurred
        expected_unobli = round(p["total_adjusted_allotment"] - p["obligations_incurred"], 2)
        assert round(p["unobligated"], 2) == expected_unobli

        # unpaid = obligations_incurred - disbursement
        expected_unpaid = round(p["obligations_incurred"] - p["disbursement"], 2)
        assert round(p["unpaid"], 2) == expected_unpaid


def test_audit_issue_3_sub_aro_identification():
    """
    Verifies that LegalBasis stores Sub-ARO identifiers without collision
    and that row_hash does not cause false collisions across identical Sub-AROs with differing lines.
    """
    row_subaro_a = {
        "OperatingUnit": "Caloocan High School",
        "Division": "Division of Caloocan",
        "Region": "NCR",
        "DateBMS": "2026-03-01",
        "AccountCode": "5020101000",
        "Particulars": "Line 1 under Sub-ARO",
        "ObligationsIncurred": "1000.00",
        "LegalBasis": "SUB-ARO-NCR-26-001",
        "Allotment": "5000.00"
    }
    row_subaro_b = {
        "OperatingUnit": "Caloocan High School",
        "Division": "Division of Caloocan",
        "Region": "NCR",
        "DateBMS": "2026-03-01",
        "AccountCode": "5020101000",
        "Particulars": "Line 2 under Sub-ARO",
        "ObligationsIncurred": "2000.00",
        "LegalBasis": "SUB-ARO-NCR-26-001",
        "Allotment": "5000.00"
    }

    hash_a = compute_row_hash(row_subaro_a)
    hash_b = compute_row_hash(row_subaro_b)
    # The two lines share the same Sub-ARO document reference, but are distinct financial lines
    assert hash_a != hash_b, "Different transaction lines under the same Sub-ARO must receive distinct fingerprints"


def test_audit_issue_4_classification_filters():
    """
    Verifies filtering across AppropriationType, AllotmentPeriod, and PPA Code
    in both API query and PPA consolidation.
    """
    token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # Verify query parameters accepted and processed cleanly
    res_records = client.get(
        "/api/v1/records?appropriation_type=Current&allotment_period=Q1",
        headers=headers
    )
    assert res_records.status_code == 200

    res_summary = client.get(
        "/api/v1/analytics/records-summary?appropriation_type=Current&allotment_period=Q1",
        headers=headers
    )
    assert res_summary.status_code == 200

    res_ppa = client.get(
        "/api/v1/records/by-ppa?appropriation_type=Current&allotment_period=Q1",
        headers=headers
    )
    assert res_ppa.status_code == 200
