import io
import pytest
from decimal import Decimal
from openpyxl import load_workbook
from app.services.calculations import to_decimal, calculate_balances
from app.services.excel_ingestion import compute_row_hash, ExcelIngestionService
from app.services.excel_export import ExcelExportService, EXPORT_HEADERS
from app.models.bms_record import BMSRecord


def test_to_decimal_handling():
    # Standard and edge cases with strict=False
    assert to_decimal(None) == Decimal("0.00")
    assert to_decimal("") == Decimal("0.00")
    assert to_decimal("   ") == Decimal("0.00")
    assert to_decimal("NA") == Decimal("0.00")
    assert to_decimal("-") == Decimal("0.00")
    assert to_decimal("1,234.56") == Decimal("1234.56")
    assert to_decimal("₱ 50,000.00") == Decimal("50000.00")
    assert to_decimal(100) == Decimal("100")
    assert to_decimal(250.75) == Decimal("250.75")
    assert to_decimal("corrupt", strict=False) == Decimal("0.00")

    # Strict mode
    with pytest.raises(ValueError):
        to_decimal("corrupt_value", strict=True)


def test_compute_row_hash_differentiation():
    base_row = {
        "OperatingUnit": "Quezon City High School",
        "Division": "Quezon City",
        "Region": "NCR",
        "DateBMS": "2026-01-15",
        "AccountCode": "5020101000",
        "UACSPAPCODE": "310100100002000",
        "PPAControl": "PPA101 - Basic Education",
        "AppropriationType": "Current",
        "AllotmentPeriod": "Q1",
        "AllotmentClass": "MOOE",
        "Particulars": "School supplies",
        "ObligationsIncurred": "5000.00",
        "Disbursement": "5000.00",
        "Appropriations": "10000.00",
        "Allotment": "10000.00",
        "TransferTo": "0.00",
        "TransferFrom": "0.00",
        "ApproAdjust": "0.00",
        "Realignment": "0.00",
        "DVAmount": "0.00",
        "FundSource": "Regular",
        "LegalBasis": "GAA 2026",
    }

    hash1 = compute_row_hash(base_row)

    # Differing ApproAdjust
    row_appro = dict(base_row, ApproAdjust="1500.00")
    hash_appro = compute_row_hash(row_appro)
    assert hash1 != hash_appro, "Row hash must differ when ApproAdjust changes"

    # Differing Realignment
    row_realign = dict(base_row, Realignment="-500.00")
    hash_realign = compute_row_hash(row_realign)
    assert hash1 != hash_realign, "Row hash must differ when Realignment changes"

    # Differing LegalBasis
    row_legal = dict(base_row, LegalBasis="SUB-ARO-NCR-2026-001")
    hash_legal = compute_row_hash(row_legal)
    assert hash1 != hash_legal, "Row hash must differ when LegalBasis changes"

    # Differing Division
    row_div = dict(base_row, Division="Manila")
    hash_div = compute_row_hash(row_div)
    assert hash1 != hash_div, "Row hash must differ when Division changes"


def test_compute_row_hash_snake_case_compatibility():
    pascal_row = {
        "OperatingUnit": "Manila Science HS",
        "DateBMS": "2026-02-01",
        "AccountCode": "5020101000",
        "Allotment": "20000.00",
        "ObligationsIncurred": "15000.00",
        "ApproAdjust": "1000.00"
    }

    snake_row = {
        "operating_unit": "Manila Science HS",
        "date_bms": "2026-02-01",
        "account_code": "5020101000",
        "allotment": "20000.00",
        "obligations_incurred": "15000.00",
        "appro_adjust": "1000.00"
    }

    assert compute_row_hash(pascal_row) == compute_row_hash(snake_row), (
        "Hash calculation must be identical for PascalCase and snake_case representations"
    )


def test_excel_export_streaming():
    records = [
        BMSRecord(
            id="rec-test-1",
            row_hash="test-hash-1",
            ppa_control="PPA350 - Madrasah",
            ppa_code="PPA350",
            ppa_description="Madrasah",
            operating_unit="Unit A",
            region="NCR",
            division="Manila",
            appropriations=Decimal("100000.00"),
            appro_adjust=Decimal("5000.00"),
            allotment=Decimal("100000.00"),
            realignment=Decimal("2000.00"),
            transfer_from=Decimal("1000.00"),
            transfer_to=Decimal("500.00"),
            obligations_incurred=Decimal("60000.00"),
            disbursement=Decimal("40000.00"),
        )
    ]

    output = io.BytesIO()
    ExcelExportService.export_to_stream(records, output)
    output.seek(0)

    wb = load_workbook(output)
    assert "Combine Sheet" in wb.sheetnames
    ws = wb["Combine Sheet"]

    rows = list(ws.iter_rows(values_only=True))
    assert len(rows) == 2  # header + 1 record
    assert list(rows[0]) == EXPORT_HEADERS

    data_row = rows[1]
    # Check 5 calculated columns (indexes 28, 29, 30, 31, 32)
    # total_adj_appro = 100000 + 5000 = 105000
    assert data_row[28] == 105000.0
    # total_adj_allotment = 100000 + 2000 + 1000 - 500 = 102500
    assert data_row[29] == 102500.0
    # unobligated = 102500 - 60000 = 42500
    assert data_row[30] == 42500.0
    # unpaid = 60000 - 40000 = 20000
    assert data_row[31] == 20000.0
    # unreleased = 105000 - 102500 = 2500
    assert data_row[32] == 2500.0
