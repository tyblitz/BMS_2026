import io
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from app.main import app
from app.core.security import create_access_token
from app.core.database import db_manager
from app.models.bms_record import BMSRecord

client = TestClient(app)


def test_ppa_consolidation_and_drilldown():
    session = next(db_manager.get_session())
    try:
        # Seed test records under two distinct unique PPAs
        r1 = BMSRecord(
            row_hash="ppa_test_hash_1",
            operating_unit="Caloocan High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            ppa_code="PPA998",
            ppa_control="PPA998 - Special Program A",
            ppa_description="Special Program A",
            appropriations=Decimal("100000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("100000.00"),
            realignment=Decimal("0.00"),
            transfer_from=Decimal("0.00"),
            transfer_to=Decimal("0.00"),
            obligations_incurred=Decimal("60000.00"),
            disbursement=Decimal("50000.00"),
            appropriation_type="Current",
            allotment_period="Q1",
            legal_basis="SUB-ARO-NCR-2026-001",
            created_by="admin",
            is_deleted=False
        )
        r2 = BMSRecord(
            row_hash="ppa_test_hash_2",
            operating_unit="Caloocan High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            ppa_code="PPA998",
            ppa_control="PPA998 - Special Program A",
            ppa_description="Special Program A",
            appropriations=Decimal("50000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("50000.00"),
            realignment=Decimal("0.00"),
            transfer_from=Decimal("0.00"),
            transfer_to=Decimal("0.00"),
            obligations_incurred=Decimal("20000.00"),
            disbursement=Decimal("15000.00"),
            appropriation_type="Current",
            allotment_period="Q1",
            legal_basis="SUB-ARO-NCR-2026-002",
            created_by="admin",
            is_deleted=False
        )
        r3 = BMSRecord(
            row_hash="ppa_test_hash_3",
            operating_unit="Caloocan High School",
            division="Division of Caloocan",
            region="National Capital Region (NCR)",
            ppa_code="PPA999",
            ppa_control="PPA999 - Special Program B",
            ppa_description="Special Program B",
            appropriations=Decimal("80000.00"),
            appro_adjust=Decimal("0.00"),
            allotment=Decimal("80000.00"),
            realignment=Decimal("0.00"),
            transfer_from=Decimal("0.00"),
            transfer_to=Decimal("0.00"),
            obligations_incurred=Decimal("40000.00"),
            disbursement=Decimal("30000.00"),
            appropriation_type="Continuing",
            allotment_period="Q2",
            legal_basis="SUB-ARO-NCR-2026-003",
            created_by="admin",
            is_deleted=False
        )
        session.add(r1)
        session.add(r2)
        session.add(r3)
        session.commit()
    finally:
        session.close()

    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Level 1: Consolidated by PPA
    resp = client.get("/api/v1/records/by-ppa", headers=headers)
    assert resp.status_code == 200
    ppa_data = resp.json()
    ppa_map = {item["ppa_code"]: item for item in ppa_data}

    # Verify PPA998 consolidation (combines r1 and r2)
    assert "PPA998" in ppa_map
    ppa998 = ppa_map["PPA998"]
    assert ppa998["transaction_count"] == 2
    assert ppa998["total_adjusted_allotment"] == 150000.0
    assert ppa998["obligations_incurred"] == 80000.0
    assert ppa998["disbursement"] == 65000.0
    assert ppa998["unobligated"] == 70000.0
    assert ppa998["unpaid"] == 15000.0

    # Verify PPA999 consolidation (r3)
    assert "PPA999" in ppa_map
    ppa999 = ppa_map["PPA999"]
    assert ppa999["transaction_count"] == 1
    assert ppa999["total_adjusted_allotment"] == 80000.0

    # 2. Level 2: Drilldown into PPA998 line items
    drill_resp = client.get("/api/v1/records?ppa_code=PPA998", headers=headers)
    assert drill_resp.status_code == 200
    drill_data = drill_resp.json()
    assert drill_data["total"] == 2
    assert all(item["ppa_code"] == "PPA998" for item in drill_data["items"])

    # 3. Test filtering by Appropriation Type and Allotment Period
    filter_resp = client.get(
        "/api/v1/records/by-ppa?appropriation_type=Continuing",
        headers=headers
    )
    assert filter_resp.status_code == 200
    filtered_ppas = filter_resp.json()
    assert any(p["ppa_code"] == "PPA999" for p in filtered_ppas)
    assert not any(p["ppa_code"] == "PPA998" for p in filtered_ppas)

    # 4. Test Export PPA Summary Excel
    export_resp = client.get("/api/v1/export/ppa-summary", headers=headers)
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    wb = load_workbook(io.BytesIO(export_resp.content))
    assert "PPA Summary" in wb.sheetnames
    ws = wb["PPA Summary"]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0][0] == "PPA Code"
    assert rows[0][1] == "PPA Description"
    assert rows[0][2] == "Transaction Count"
    assert len(rows) >= 3 # Header + at least PPA998 and PPA999
