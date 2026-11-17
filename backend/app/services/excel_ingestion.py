import hashlib
import re
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

REQUIRED_COLUMNS = [
    "DateBMS", "AccountCode", "ObligationsIncurred", "Disbursement",
    "Allotment", "OperatingUnit"
]

HASH_FIELD_SPECS = [
    ("OperatingUnit", "operating_unit", False),
    ("Division", "division", False),
    ("Region", "region", False),
    ("DateBMS", "date_bms", False),
    ("AccountCode", "account_code", False),
    ("UACSPAPCODE", "uacs_pap_code", False),
    ("PPAControl", "ppa_control", False),
    ("AppropriationType", "appropriation_type", False),
    ("AllotmentPeriod", "allotment_period", False),
    ("AllotmentClass", "allotment_class", False),
    ("Particulars", "particulars", False),
    ("ObligationsIncurred", "obligations_incurred", True),
    ("Disbursement", "disbursement", True),
    ("Appropriations", "appropriations", True),
    ("Allotment", "allotment", True),
    ("TransferTo", "transfer_to", True),
    ("TransferFrom", "transfer_from", True),
    ("ApproAdjust", "appro_adjust", True),
    ("Realignment", "realignment", True),
    ("DVAmount", "dv_amount", True),
    ("FundSource", "fund_source", False),
    ("LegalBasis", "legal_basis", False),
    ("OrgCodeUACS", "org_code_uacs", False),
    ("Locality", "locality", False),
    ("RC", "rc", False),
]


def compute_row_hash(row: dict) -> str:
    """
    Computes a deterministic SHA-256 fingerprint from 25 core business, organizational,
    and financial adjustment fields. Normalizes numeric amounts to 2 decimal places to
    guarantee cross-system idempotency while avoiding false duplicate collisions on realignments.
    Supports both PascalCase (Excel) and snake_case (API model) keys.
    """
    parts = []
    for pascal_k, snake_k, is_numeric in HASH_FIELD_SPECS:
        val = row.get(pascal_k) if pascal_k in row else row.get(snake_k)
        if is_numeric:
            dec = to_decimal(val, strict=False)
            parts.append(f"{dec:.2f}")
        else:
            parts.append(str(val or "").strip())

    sig = "|".join(parts)
    return hashlib.sha256(sig.encode("utf-8")).hexdigest()


class ExcelIngestionService:
    @staticmethod
    def parse_file(file_path_or_bytes: Any) -> Generator[dict, None, None]:
        """
        Memory-safe streaming parser using Calamine (Rust engine).
        Validates template schema and streams rows one-by-one with constant minimal memory footprint.
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

        # Validate headers against required columns
        header_set_clean = {re.sub(r"[_\s]+", "", h).lower() for h in headers}
        missing_required = []
        for req in REQUIRED_COLUMNS:
            req_clean = re.sub(r"[_\s]+", "", req).lower()
            if req_clean not in header_set_clean:
                missing_required.append(req)

        if missing_required:
            raise ValueError(
                f"Invalid Excel template: sheet '{target_sheet}' is missing required columns: {', '.join(missing_required)}"
            )

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
        Ingests records with strict deduplication, PPA normalization, and RBAC validation.
        Skips rows whose row_hash already exists in the database.
        """
        total_rows = 0
        inserted_count = 0
        duplicate_count = 0
        skipped_scope_count = 0
        errors = []

        batch = []
        batch_hashes = set()

        def parse_numeric(field_name: str, raw_val: Any) -> Decimal:
            try:
                return to_decimal(raw_val, strict=True)
            except ValueError:
                errors.append(f"Row {total_rows}: '{field_name}' invalid numeric value '{raw_val}', defaulted to 0.00")
                return Decimal("0.00")

        try:
            for raw_row in cls.parse_file(file_path_or_bytes):
                total_rows += 1
                
                # Compute 25-field deterministic hash
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

                raw_ppa = str(raw_row.get("PPAControl") or "").strip()
                ppa_code = None
                ppa_description = None
                if raw_ppa:
                    m = re.match(r"^(PPA\d+)\s*-\s*(.+)$", raw_ppa)
                    if m:
                        ppa_code = m.group(1)
                        ppa_description = m.group(2)
                    else:
                        ppa_code = raw_ppa[:20]
                        ppa_description = raw_ppa

                record = BMSRecord(
                    row_hash=row_hash,
                    ppa_control=raw_ppa or None,
                    ppa_code=ppa_code,
                    ppa_description=ppa_description,
                    appropriation_type=str(raw_row.get("AppropriationType") or "").strip() or None,
                    allotment_period=str(raw_row.get("AllotmentPeriod") or "").strip() or None,
                    allotment_class=str(raw_row.get("AllotmentClass") or "").strip() or None,
                    date_bms=str(raw_row.get("DateBMS") or "").strip() or None,
                    account_code=str(raw_row.get("AccountCode") or "").strip() or None,
                    obligations_incurred=parse_numeric("ObligationsIncurred", raw_row.get("ObligationsIncurred")),
                    disbursement=parse_numeric("Disbursement", raw_row.get("Disbursement")),
                    appropriations=parse_numeric("Appropriations", raw_row.get("Appropriations")),
                    allotment=parse_numeric("Allotment", raw_row.get("Allotment")),
                    transfer_to=parse_numeric("TransferTo", raw_row.get("TransferTo")),
                    transfer_from=parse_numeric("TransferFrom", raw_row.get("TransferFrom")),
                    particulars=str(raw_row.get("Particulars") or "").strip() or None,
                    uacs_pap_code=str(raw_row.get("UACSPAPCODE") or "").strip() or None,
                    dv_amount=parse_numeric("DVAmount", raw_row.get("DVAmount")),
                    region=region or "Default Region",
                    division=division or "Default Division",
                    operating_unit=operating_unit or "Default Unit",
                    org_code_uacs=str(raw_row.get("OrgCodeUACS") or "").strip() or None,
                    appro_adjust=parse_numeric("ApproAdjust", raw_row.get("ApproAdjust")),
                    realignment=parse_numeric("Realignment", raw_row.get("Realignment")),
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

        except Exception:
            db.rollback()
            raise

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
            try:
                db.bulk_save_objects(to_insert)
                db.commit()
            except Exception:
                db.rollback()
                raise

        return len(to_insert), duplicates
