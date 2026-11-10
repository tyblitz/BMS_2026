import hashlib
from decimal import Decimal
from typing import Generator, Any, Optional
from python_calamine import load_workbook
from sqlalchemy.orm import Session
from app.models.bms_record import BMSRecord
from app.services.calculations import to_decimal

EXPECTED_HEADERS = [
    "PPAControl", "AppropriationType", "AllotmentPeriod", "AllotmentClass",
    "DateBMS", "AccountCode", "ObligationsIncurred", "Disbursement",
    "Appropriations", "Allotment", "TransferTo", "TransferFrom",
    "Particulars", "UACSPAPCODE", "DVAmount", "Region", "Division",
    "OperatingUnit", "OrgCodeUACS", "ApproAdjust", "Realignment",
    "FundSource", "Locality", "LegalBasis", "RC", "Reg", "CCETCode",
    "Ledger", "TOTAL ADJUSTED APPRO", "TOTAL ADJUSTED ALLOTMENT ",
    "UNOBLIGATED", "UNPAID", "UNRELEASED"
]


def compute_row_hash(row: dict) -> str:
    """
    Computes a deterministic SHA-256 fingerprint from core business fields.
    Normalizes numeric amounts to 2 decimal places to guarantee cross-system idempotency.
    """
    numeric_keys = {
        "ObligationsIncurred", "Disbursement", "Appropriations",
        "Allotment", "TransferTo", "TransferFrom", "DVAmount"
    }
    parts = []
    for k in [
        "OperatingUnit", "DateBMS", "AccountCode", "UACSPAPCODE",
        "Particulars", "ObligationsIncurred", "Disbursement",
        "Appropriations", "Allotment", "FundSource", "TransferTo",
        "TransferFrom", "DVAmount"
    ]:
        val = row.get(k)
        if k in numeric_keys:
            parts.append(f"{to_decimal(val):.2f}")
        else:
            parts.append(str(val or "").strip())

    sig = "|".join(parts)
    return hashlib.sha256(sig.encode("utf-8")).hexdigest()


class ExcelIngestionService:
    @staticmethod
    def parse_file(file_path_or_bytes: Any) -> Generator[dict, None, None]:
        """
        Memory-safe streaming parser using Calamine (Rust engine).
        Streams rows one-by-one with constant minimal memory footprint.
        """
        wb = load_workbook(file_path_or_bytes)
        sheet_names = wb.sheet_names
        
        target_sheet = "Combine Sheet" if "Combine Sheet" in sheet_names else sheet_names[0]
        rows_iter = iter(wb.get_sheet_by_name(target_sheet).to_python())
        
        # Read header row
        try:
            raw_headers = next(rows_iter)
        except StopIteration:
            return

        headers = [str(h).strip() if h is not None else f"col_{idx}" for idx, h in enumerate(raw_headers)]

        for row in rows_iter:
            if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            row_dict = {}
            for idx, val in enumerate(row):
                if idx < len(headers):
                    col_name = headers[idx]
                    row_dict[col_name] = val
            yield row_dict

    @classmethod
    def ingest_records(
        cls,
        file_path_or_bytes: Any,
        db: Session,
        uploaded_by: str,
        user_role: Optional[str] = None,
        user_scope: Optional[dict] = None,
        batch_size: int = 1000
    ) -> dict:
        """
        Ingests records with strict deduplication and RBAC validation.
        Skips rows whose row_hash already exists in the database.
        """
        total_rows = 0
        inserted_count = 0
        duplicate_count = 0
        skipped_scope_count = 0
        errors = []

        batch = []
        batch_hashes = set()

        for raw_row in cls.parse_file(file_path_or_bytes):
            total_rows += 1
            
            # Map raw Excel fields to normalized dictionary
            row_hash = compute_row_hash(raw_row)

            # In-file duplicate check
            if row_hash in batch_hashes:
                duplicate_count += 1
                continue
            batch_hashes.add(row_hash)

            operating_unit = str(raw_row.get("OperatingUnit") or "").strip()
            division = str(raw_row.get("Division") or "").strip()
            region = str(raw_row.get("Region") or "").strip()

            # RBAC Scope Check during upload
            if user_role and user_scope:
                if user_role == "school" and user_scope.get("school_name"):
                    if operating_unit != user_scope["school_name"]:
                        skipped_scope_count += 1
                        continue
                elif user_role == "sdo" and user_scope.get("division"):
                    if division != user_scope["division"]:
                        skipped_scope_count += 1
                        continue
                elif user_role == "region" and user_scope.get("region"):
                    if region != user_scope["region"]:
                        skipped_scope_count += 1
                        continue

            record = BMSRecord(
                row_hash=row_hash,
                ppa_control=str(raw_row.get("PPAControl") or "").strip() or None,
                appropriation_type=str(raw_row.get("AppropriationType") or "").strip() or None,
                allotment_period=str(raw_row.get("AllotmentPeriod") or "").strip() or None,
                allotment_class=str(raw_row.get("AllotmentClass") or "").strip() or None,
                date_bms=str(raw_row.get("DateBMS") or "").strip() or None,
                account_code=str(raw_row.get("AccountCode") or "").strip() or None,
                obligations_incurred=to_decimal(raw_row.get("ObligationsIncurred")),
                disbursement=to_decimal(raw_row.get("Disbursement")),
                appropriations=to_decimal(raw_row.get("Appropriations")),
                allotment=to_decimal(raw_row.get("Allotment")),
                transfer_to=to_decimal(raw_row.get("TransferTo")),
                transfer_from=to_decimal(raw_row.get("TransferFrom")),
                particulars=str(raw_row.get("Particulars") or "").strip() or None,
                uacs_pap_code=str(raw_row.get("UACSPAPCODE") or "").strip() or None,
                dv_amount=to_decimal(raw_row.get("DVAmount")),
                region=region or "Default Region",
                division=division or "Default Division",
                operating_unit=operating_unit or "Default Unit",
                org_code_uacs=str(raw_row.get("OrgCodeUACS") or "").strip() or None,
                appro_adjust=to_decimal(raw_row.get("ApproAdjust")),
                realignment=to_decimal(raw_row.get("Realignment")),
                fund_source=str(raw_row.get("FundSource") or "").strip() or None,
                locality=str(raw_row.get("Locality") or "").strip() or None,
                legal_basis=str(raw_row.get("LegalBasis") or "").strip() or None,
                rc=str(raw_row.get("RC") or "").strip() or None,
                reg=str(raw_row.get("Reg") or "NA").strip(),
                ccet_code=str(raw_row.get("CCETCode") or "NA").strip(),
                ledger=str(raw_row.get("Ledger") or "NA").strip(),
                created_by=uploaded_by,
                is_deleted=False
            )
            batch.append(record)

            if len(batch) >= batch_size:
                inserted, dups = cls._flush_batch(batch, db)
                inserted_count += inserted
                duplicate_count += dups
                batch = []
                batch_hashes.clear()

        if batch:
            inserted, dups = cls._flush_batch(batch, db)
            inserted_count += inserted
            duplicate_count += dups

        return {
            "total_rows": total_rows,
            "inserted": inserted_count,
            "duplicates_skipped": duplicate_count,
            "skipped_out_of_scope": skipped_scope_count,
            "errors": errors
        }

    @staticmethod
    def _flush_batch(records: list[BMSRecord], db: Session) -> tuple[int, int]:
        """Flushes a batch to DB, checking for existing row_hashes to skip duplicates."""
        if not records:
            return 0, 0
        
        hashes = [r.row_hash for r in records]
        # Query existing active hashes in database
        existing_hashes = set(
            row[0] for row in db.query(BMSRecord.row_hash)
            .filter(BMSRecord.row_hash.in_(hashes), BMSRecord.is_deleted == False)
            .all()
        )

        to_insert = [r for r in records if r.row_hash not in existing_hashes]
        duplicates = len(records) - len(to_insert)

        if to_insert:
            db.bulk_save_objects(to_insert)
            db.commit()

        return len(to_insert), duplicates
