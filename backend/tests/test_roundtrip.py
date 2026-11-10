import io
import os
from pathlib import Path
from decimal import Decimal
from python_calamine import load_workbook
from app.core.database import db_manager
from app.models.bms_record import BMSRecord
from app.services.excel_ingestion import ExcelIngestionService, compute_row_hash
from app.services.excel_export import ExcelExportService, EXPORT_HEADERS
from app.services.calculations import calculate_balances

FIXTURE_PATH = Path("backend/tests/fixtures/sample_tempTable.xlsx")
BENCHMARK_PATH = Path("CONSO tempTable as of September 30, 2026.xlsx")


def test_end_to_end_roundtrip_ms_access_compatibility():
    """
    Validates end-to-end roundtrip workflow:
    1. Ingestion from Excel
    2. Modification / Consolidation in Database
    3. Streaming Export to Excel
    4. Structural and mathematical verification of exported Excel for MS Access BMS
    5. Re-ingestion verification (idempotency)
    """
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.commit()

        # Step 1: Ingest sample file
        res = ExcelIngestionService.ingest_records(
            file_path_or_bytes=str(FIXTURE_PATH),
            db=session,
            uploaded_by="roundtrip_tester"
        )
        assert res["total_rows"] == 50
        assert res["inserted"] == 50

        # Step 2: Simulate financial operations (e.g. increase obligation and disbursement on a record)
        rec = session.query(BMSRecord).first()
        rec.obligations_incurred = Decimal("15500.00")
        rec.disbursement = Decimal("10250.50")
        rec.edited_by = "roundtrip_tester"
        # Update row_hash to reflect modified transaction numbers
        hash_input = {
            "OperatingUnit": rec.operating_unit,
            "DateBMS": rec.date_bms,
            "AccountCode": rec.account_code,
            "UACSPAPCODE": rec.uacs_pap_code,
            "Particulars": rec.particulars,
            "ObligationsIncurred": rec.obligations_incurred,
            "Disbursement": rec.disbursement,
            "Appropriations": rec.appropriations,
            "Allotment": rec.allotment,
            "FundSource": rec.fund_source,
            "TransferTo": rec.transfer_to,
            "TransferFrom": rec.transfer_from,
            "DVAmount": rec.dv_amount
        }
        rec.row_hash = compute_row_hash(hash_input)
        session.commit()

        # Step 3: Stream Export
        output = io.BytesIO()
        records = session.query(BMSRecord).filter(BMSRecord.is_deleted == False).order_by(BMSRecord.operating_unit).all()
        ExcelExportService.export_to_stream(records, output)
        exported_bytes = output.getvalue()
        assert len(exported_bytes) > 0

        # Step 4: Structural Verification of Exported Excel
        wb = load_workbook(io.BytesIO(exported_bytes))
        assert "Combine Sheet" in wb.sheet_names, "Workbook must contain 'Combine Sheet' for MS Access BMS"
        sheet = wb.get_sheet_by_name("Combine Sheet")
        rows = list(sheet.to_python())

        # Header check: exactly 33 columns in exact order
        header_row = rows[0]
        assert len(header_row) == 33
        assert header_row == EXPORT_HEADERS
        assert header_row[29] == "TOTAL ADJUSTED ALLOTMENT ", "Must include trailing space on column 29"

        # Data rows check
        assert len(rows) == 51 # 1 header + 50 data rows

        # Verify mathematical consistency across every single row in the exported file
        for r_idx, row in enumerate(rows[1:], start=2):
            appro = float(row[8] or 0)       # Col I: Appropriations
            allot = float(row[9] or 0)       # Col J: Allotment
            trans_to = float(row[10] or 0)   # Col K: TransferTo
            trans_from = float(row[11] or 0) # Col L: TransferFrom
            obli = float(row[6] or 0)        # Col G: ObligationsIncurred
            disb = float(row[7] or 0)        # Col H: Disbursement
            appro_adj = float(row[19] or 0)  # Col T: ApproAdjust
            realign = float(row[20] or 0)    # Col U: Realignment

            tot_adj_appro = float(row[28])   # Col AC
            tot_adj_allot = float(row[29])   # Col AD
            unobligated = float(row[30])     # Col AE
            unpaid = float(row[31])          # Col AF
            unreleased = float(row[32])      # Col AG

            # Formula 1: TOTAL ADJUSTED APPRO = Appropriations + ApproAdjust
            assert round(tot_adj_appro, 2) == round(appro + appro_adj, 2)
            # Formula 2: TOTAL ADJUSTED ALLOTMENT = Allotment + Realignment + TransferFrom - TransferTo
            assert round(tot_adj_allot, 2) == round(allot + realign + trans_from - trans_to, 2)
            # Formula 3: UNOBLIGATED = TOTAL ADJUSTED ALLOTMENT - ObligationsIncurred
            assert round(unobligated, 2) == round(tot_adj_allot - obli, 2)
            # Formula 4: UNPAID = ObligationsIncurred - Disbursement
            assert round(unpaid, 2) == round(obli - disb, 2)
            # Formula 5: UNRELEASED = TOTAL ADJUSTED APPRO - TOTAL ADJUSTED ALLOTMENT
            assert round(unreleased, 2) == round(tot_adj_appro - tot_adj_allot, 2)

        # Step 5: Re-ingestion check (Idempotency)
        # Ingesting the exported file back should detect existing records and insert 0 duplicates
        reingest_res = ExcelIngestionService.ingest_records(
            file_path_or_bytes=io.BytesIO(exported_bytes),
            db=session,
            uploaded_by="roundtrip_retester"
        )
        assert reingest_res["total_rows"] == 50
        assert reingest_res["inserted"] == 0
        assert reingest_res["duplicates_skipped"] == 50

    finally:
        session.close()


def test_large_benchmark_streaming_capacity():
    """
    Validates streaming ingestion on large files without memory exhaustion.
    If the benchmark file exists locally, streams the first 1,000 rows.
    """
    if BENCHMARK_PATH.exists():
        row_count = 0
        for row in ExcelIngestionService.parse_file(str(BENCHMARK_PATH)):
            row_count += 1
            if row_count >= 1000:
                break
        assert row_count == 1000
