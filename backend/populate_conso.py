"""
Population and Seeding Script:
1. Resets and initializes the database fresh.
2. Seeds Admin, 1 Regional Office (NCR), 16 SDO accounts, and all 194 School accounts.
3. High-speed bulk ingests all ~209,309 data rows from 'CONSO tempTable as of September 30, 2026.xlsx'.
4. Generates a complete user reference document in 'docs/ACCOUNTS_LIST.md'.
"""
import sys
import os
import re
import uuid
import time
from pathlib import Path
from decimal import Decimal

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from python_calamine import load_workbook
from sqlalchemy import text
from app.core.database import db_manager
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User
from app.models.bms_record import BMSRecord
from app.services.excel_ingestion import compute_row_hash
from app.services.calculations import to_decimal

EXCEL_FILE = "CONSO tempTable as of September 30, 2026.xlsx"
DEFAULT_PASSWORD = "Password123!"
ADMIN_PASSWORD = "Admin123!"

SDO_MAP = {
    "Division of Caloocan": "sdo_caloocan",
    "Division of Las Piñas": "sdo_las_pinas",
    "Division of Makati": "sdo_makati",
    "Division of Malabon City": "sdo_malabon_city",
    "Division of Mandaluyong": "sdo_mandaluyong",
    "Division of Manila": "sdo_manila",
    "Division of Marikina": "sdo_marikina",
    "Division of Muntinlupa": "sdo_muntinlupa",
    "Division of Navotas City": "sdo_navotas_city",
    "Division of Parañaque": "sdo_paranaque",
    "Division of Pasay City": "sdo_pasay_city",
    "Division of Pasig City": "sdo_pasig_city",
    "Division of Quezon City": "sdo_quezon_city",
    "Division of San Juan City": "sdo_san_juan_city",
    "Division of Taguig and Pateros": "sdo_taguig_pateros",
    "Division of Valenzuela": "sdo_valenzuela",
}


def slugify(text: str) -> str:
    s = text.lower()
    # Replace non-alphanumeric with underscore
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:45]


def run_population():
    start_time = time.time()
    print("=" * 70)
    print("  DepEd NCR BURS — Database Reset & Population Engine")
    print("=" * 70)

    # 1. Reset Database Schema
    print("Step 1: Resetting database tables...")
    Base.metadata.drop_all(bind=db_manager.engine)
    Base.metadata.create_all(bind=db_manager.engine)
    print("✓ All tables dropped and re-created fresh.")

    # Apply SQLite performance optimizations for initial bulk load
    if "sqlite" in db_manager.active_url:
        with db_manager.engine.connect() as conn:
            conn.execute(text("PRAGMA synchronous = OFF;"))
            conn.execute(text("PRAGMA journal_mode = MEMORY;"))
            conn.commit()

    session = next(db_manager.get_session())

    try:
        # 2. Inspect Excel to map distinct Schools & SDOs
        print(f"\nStep 2: Inspecting '{EXCEL_FILE}' for school and division mappings...")
        wb = load_workbook(EXCEL_FILE)
        sheet = wb.get_sheet_by_name("Combine Sheet")
        rows_iter = iter(sheet.to_python())
        headers = next(rows_iter)

        unit_idx = headers.index("OperatingUnit")
        div_idx = headers.index("Division")
        reg_idx = headers.index("Region")

        # Map schools -> (division, region)
        schools_map = {}
        for r in rows_iter:
            unit = str(r[unit_idx] or "").strip()
            div = str(r[div_idx] or "").strip()
            reg = str(r[reg_idx] or "").strip()
            if unit and unit not in schools_map:
                schools_map[unit] = (div, reg)

        print(f"✓ Found {len(schools_map)} distinct schools across {len(SDO_MAP)} SDOs.")

        # 3. Provision User Accounts
        print("\nStep 3: Provisioning user accounts...")
        user_records = []
        accounts_doc = []

        hashed_admin_pwd = get_password_hash(ADMIN_PASSWORD)
        hashed_default_pwd = get_password_hash(DEFAULT_PASSWORD)

        # 3.1 Admin
        user_records.append({
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@deped.gov.ph",
            "hashed_password": hashed_admin_pwd,
            "role": "admin",
            "school_name": None,
            "division": None,
            "region": None,
            "is_active": True,
            "is_deleted": False,
            "created_by": "system_population"
        })
        accounts_doc.append(("admin", ADMIN_PASSWORD, "Administrator", "Full System (All Offices)"))

        # 3.2 Regional Office (NCR)
        user_records.append({
            "id": str(uuid.uuid4()),
            "username": "ro_ncr",
            "email": "ncr@deped.gov.ph",
            "hashed_password": hashed_default_pwd,
            "role": "region",
            "school_name": None,
            "division": None,
            "region": "National Capital Region (NCR)",
            "is_active": True,
            "is_deleted": False,
            "created_by": "system_population"
        })
        accounts_doc.append(("ro_ncr", DEFAULT_PASSWORD, "Regional Office", "National Capital Region (NCR)"))

        # 3.3 The 16 SDO Accounts
        for div_name, sdo_username in sorted(SDO_MAP.items()):
            user_records.append({
                "id": str(uuid.uuid4()),
                "username": sdo_username,
                "email": f"{sdo_username}@deped.gov.ph",
                "hashed_password": hashed_default_pwd,
                "role": "sdo",
                "school_name": None,
                "division": div_name,
                "region": "National Capital Region (NCR)",
                "is_active": True,
                "is_deleted": False,
                "created_by": "system_population"
            })
            accounts_doc.append((sdo_username, DEFAULT_PASSWORD, "SDO Consolidator", div_name))

        # 3.4 The 194 School Accounts
        used_school_usernames = set()
        for school_name, (div, reg) in sorted(schools_map.items()):
            base_slug = "sch_" + slugify(school_name)
            username = base_slug
            idx = 2
            while username in used_school_usernames:
                username = f"{base_slug}_{idx}"
                idx += 1
            used_school_usernames.add(username)

            user_records.append({
                "id": str(uuid.uuid4()),
                "username": username,
                "email": f"{username}@deped.gov.ph",
                "hashed_password": hashed_default_pwd,
                "role": "school",
                "school_name": school_name,
                "division": div,
                "region": reg or "National Capital Region (NCR)",
                "is_active": True,
                "is_deleted": False,
                "created_by": "system_population"
            })
            accounts_doc.append((username, DEFAULT_PASSWORD, "School Encoder", f"{school_name} ({div})"))

        session.bulk_insert_mappings(User, user_records)
        session.commit()
        print(f"✓ Provisioned {len(user_records)} accounts (1 Admin, 1 Regional, 16 SDOs, {len(schools_map)} Schools).")

        # 4. Ingest All 209,309 Budget Records
        print("\nStep 4: Streaming & ingesting 209,309 transaction rows...")
        # Re-initialize sheet iterator for full data ingestion
        sheet = wb.get_sheet_by_name("Combine Sheet")
        rows_iter = iter(sheet.to_python())
        raw_headers = next(rows_iter)
        col_map = {name: idx for idx, name in enumerate(raw_headers)}

        batch = []
        batch_size = 5000
        total_ingested = 0
        duplicates_skipped = 0
        seen_hashes = set()

        # Pre-cache header indices
        c_ppa = col_map.get("PPAControl")
        c_app_type = col_map.get("AppropriationType")
        c_allot_per = col_map.get("AllotmentPeriod")
        c_allot_cls = col_map.get("AllotmentClass")
        c_date = col_map.get("DateBMS")
        c_acct = col_map.get("AccountCode")
        c_obli = col_map.get("ObligationsIncurred")
        c_disb = col_map.get("Disbursement")
        c_appro = col_map.get("Appropriations")
        c_allot = col_map.get("Allotment")
        c_trans_to = col_map.get("TransferTo")
        c_trans_from = col_map.get("TransferFrom")
        c_part = col_map.get("Particulars")
        c_uacs = col_map.get("UACSPAPCODE")
        c_dv = col_map.get("DVAmount")
        c_reg = col_map.get("Region")
        c_div = col_map.get("Division")
        c_unit = col_map.get("OperatingUnit")
        c_org = col_map.get("OrgCodeUACS")
        c_appro_adj = col_map.get("ApproAdjust")
        c_realign = col_map.get("Realignment")
        c_fund = col_map.get("FundSource")
        c_loc = col_map.get("Locality")
        c_leg = col_map.get("LegalBasis")
        c_rc = col_map.get("RC")
        c_reg_s = col_map.get("Reg")
        c_ccet = col_map.get("CCETCode")
        c_led = col_map.get("Ledger")

        row_counter = 0
        for r in rows_iter:
            row_counter += 1
            unit = r[c_unit] if c_unit is not None else None
            # Skip empty rows (the trailing 800k blank rows)
            if not unit or not str(unit).strip():
                continue

            op_unit_str = str(unit).strip()
            date_bms_str = str(r[c_date] or "").strip()
            acct_code_str = str(r[c_acct] or "").strip()
            uacs_pap_str = str(r[c_uacs] or "").strip()
            particulars_str = str(r[c_part] or "").strip() or None

            obli_val = to_decimal(r[c_obli])
            disb_val = to_decimal(r[c_disb])
            appro_val = to_decimal(r[c_appro])
            allot_val = to_decimal(r[c_allot])
            trans_to_val = to_decimal(r[c_trans_to])
            trans_from_val = to_decimal(r[c_trans_from])
            dv_val = to_decimal(r[c_dv])
            fund_source_str = str(r[c_fund] or "").strip() or None

            hash_input = {
                "OperatingUnit": op_unit_str,
                "DateBMS": date_bms_str,
                "AccountCode": acct_code_str,
                "UACSPAPCODE": uacs_pap_str,
                "Particulars": particulars_str,
                "ObligationsIncurred": obli_val,
                "Disbursement": disb_val,
                "Appropriations": appro_val,
                "Allotment": allot_val,
                "FundSource": fund_source_str,
                "TransferTo": trans_to_val,
                "TransferFrom": trans_from_val,
                "DVAmount": dv_val
            }
            row_hash = compute_row_hash(hash_input)

            if row_hash in seen_hashes:
                duplicates_skipped += 1
                continue
            seen_hashes.add(row_hash)

            record_map = {
                "id": str(uuid.uuid4()),
                "row_hash": row_hash,
                "ppa_control": str(r[c_ppa] or "").strip() or None,
                "appropriation_type": str(r[c_app_type] or "").strip() or None,
                "allotment_period": str(r[c_allot_per] or "").strip() or None,
                "allotment_class": str(r[c_allot_cls] or "").strip() or None,
                "date_bms": date_bms_str or None,
                "account_code": acct_code_str or None,
                "obligations_incurred": obli_val,
                "disbursement": disb_val,
                "appropriations": appro_val,
                "allotment": allot_val,
                "transfer_to": trans_to_val,
                "transfer_from": trans_from_val,
                "particulars": particulars_str,
                "uacs_pap_code": uacs_pap_str or None,
                "dv_amount": dv_val,
                "region": str(r[c_reg] or "National Capital Region (NCR)").strip(),
                "division": str(r[c_div] or "Default Division").strip(),
                "operating_unit": op_unit_str,
                "org_code_uacs": str(r[c_org] or "").strip() or None,
                "appro_adjust": to_decimal(r[c_appro_adj]),
                "realignment": to_decimal(r[c_realign]),
                "fund_source": fund_source_str,
                "locality": str(r[c_loc] or "School").strip(),
                "legal_basis": str(r[c_leg] or "").strip() or None,
                "rc": str(r[c_rc] or "SCH-IU").strip() or None,
                "reg": str(r[c_reg_s] or "NA").strip(),
                "ccet_code": str(r[c_ccet] or "NA").strip(),
                "ledger": str(r[c_led] or "NA").strip(),
                "is_deleted": False,
                "created_by": "initial_population"
            }
            batch.append(record_map)

            if len(batch) >= batch_size:
                session.bulk_insert_mappings(BMSRecord, batch)
                session.commit()
                total_ingested += len(batch)
                batch.clear()
                sys.stdout.write(f"\r  -> Ingested {total_ingested:,} rows...")
                sys.stdout.flush()

        if batch:
            session.bulk_insert_mappings(BMSRecord, batch)
            session.commit()
            total_ingested += len(batch)
            batch.clear()

        print(f"\n✓ Completed Ingestion: {total_ingested:,} active rows inserted ({duplicates_skipped} duplicates skipped).")

        # 5. Generate Documentation: docs/ACCOUNTS_LIST.md
        print("\nStep 5: Generating 'docs/ACCOUNTS_LIST.md'...")
        docs_path = Path("docs/ACCOUNTS_LIST.md")
        with open(docs_path, "w", encoding="utf-8") as f:
            f.write("# DepEd NCR BURS — User Accounts & Scope Directory\n\n")
            f.write(f"Total Provisioned Accounts: **{len(accounts_doc)}**\n\n")
            f.write("## 1. System Administration & Regional Office\n\n")
            f.write("| Username | Password | Role | Assigned Scope |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for u, p, r, s in accounts_doc[:2]:
                f.write(f"| **`{u}`** | `{p}` | {r} | {s} |\n")

            f.write("\n## 2. Schools Division Offices (The 16 SDOs)\n\n")
            f.write("| Username | Password | Role | Division Scope |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for u, p, r, s in accounts_doc[2:18]:
                f.write(f"| **`{u}`** | `{p}` | {r} | {s} |\n")

            f.write(f"\n## 3. School Encoders (194 Schools)\n\n")
            f.write("| Username | Password | Role | School & Division Scope |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for u, p, r, s in accounts_doc[18:]:
                f.write(f"| **`{u}`** | `{p}` | {r} | {s} |\n")

        print("✓ Created docs/ACCOUNTS_LIST.md with all 212 accounts cataloged.")

    finally:
        session.close()

    elapsed = time.time() - start_time
    print("=" * 70)
    print(f"  POPULATION FINISHED SUCCESSFULLY in {elapsed:.1f} seconds!")
    print("=" * 70)


if __name__ == "__main__":
    run_population()

