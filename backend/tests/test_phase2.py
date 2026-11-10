import io
from pathlib import Path
from python_calamine import load_workbook
from openpyxl import load_workbook as openpyxl_load
from app.core.database import db_manager
from app.services.excel_ingestion import ExcelIngestionService, compute_row_hash
from app.services.excel_export import ExcelExportService, EXPORT_HEADERS
from app.models.bms_record import BMSRecord

FIXTURE_PATH = Path("backend/tests/fixtures/sample_tempTable.xlsx")


def test_streaming_ingestion_and_deduplication():
    session = next(db_manager.get_session())
    try:
        # Clean any existing test records
        session.query(BMSRecord).delete()
        session.commit()

        # 1. First Ingestion
        res1 = ExcelIngestionService.ingest_records(
            file_path_or_bytes=str(FIXTURE_PATH),
            db=session,
            uploaded_by="test_admin"
        )
        assert res1["total_rows"] == 50
        assert res1["inserted"] == 50
        assert res1["duplicates_skipped"] == 0

        # Verify records in database
        count = session.query(BMSRecord).filter(BMSRecord.is_deleted == False).count()
        assert count == 50

        # 2. Re-uploading the same file: strict deduplication
        res2 = ExcelIngestionService.ingest_records(
            file_path_or_bytes=str(FIXTURE_PATH),
            db=session,
            uploaded_by="test_admin"
        )
        assert res2["total_rows"] == 50
        assert res2["inserted"] == 0
        assert res2["duplicates_skipped"] == 50

        # Count should remain exactly 50
        count_after = session.query(BMSRecord).filter(BMSRecord.is_deleted == False).count()
        assert count_after == 50

    finally:
        session.close()


def test_scoped_ingestion_filter():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.commit()

        # Upload as a school user for a school that does not match the file's schools
        res = ExcelIngestionService.ingest_records(
            file_path_or_bytes=str(FIXTURE_PATH),
            db=session,
            uploaded_by="school_user_1",
            user_role="school",
            user_scope={"school_name": "NonExistent School"}
        )
        assert res["inserted"] == 0
        assert res["skipped_out_of_scope"] == 50
    finally:
        session.close()


def test_streaming_export_compatibility():
    session = next(db_manager.get_session())
    try:
        session.query(BMSRecord).delete()
        session.commit()

        # Ingest 50 sample rows
        ExcelIngestionService.ingest_records(
            file_path_or_bytes=str(FIXTURE_PATH),
            db=session,
            uploaded_by="test_admin"
        )

        records = session.query(BMSRecord).filter(BMSRecord.is_deleted == False).all()
        assert len(records) == 50

        # Export to in-memory stream
        stream = io.BytesIO()
        ExcelExportService.export_to_stream(records, stream)
        stream_bytes = stream.getvalue()
        assert len(stream_bytes) > 0

        # Parse exported workbook
        exported_wb = load_workbook(io.BytesIO(stream_bytes))
        assert "Combine Sheet" in exported_wb.sheet_names
        sheet = exported_wb.get_sheet_by_name("Combine Sheet")
        rows = list(sheet.to_python())

        # Check headers
        header_row = rows[0]
        assert len(header_row) == 33
        assert header_row == EXPORT_HEADERS
        # Check specific critical headers
        assert header_row[29] == "TOTAL ADJUSTED ALLOTMENT " # with trailing space
        assert header_row[30] == "UNOBLIGATED"
        assert header_row[31] == "UNPAID"
        assert header_row[32] == "UNRELEASED"

        # Check data row count (1 header + 50 rows)
        assert len(rows) == 51

        # Check sample calculated value in first data row
        row1 = rows[1]
        appro = row1[8]
        appro_adj = row1[19]
        tot_adj_appro = row1[28]
        assert tot_adj_appro == (appro + appro_adj)

    finally:
        session.close()

